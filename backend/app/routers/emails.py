import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Influencer, OutreachEmail, LeadStatus
from app.schemas import (
    EmailGenerateRequest,
    EmailUpdateRequest,
    OutreachEmailResponse,
    SendEmailsRequest
)
from app.services.claude_service import claude_service
from app.services.gmail_service import gmail_service
from app.services.sheets_service import sheets_service
from app.config import settings

router = APIRouter(prefix="/emails", tags=["Email Outreach"])
logger = logging.getLogger("emails_router")


@router.post("/generate", response_model=List[OutreachEmailResponse])
def generate_cold_emails(payload: EmailGenerateRequest, db: Session = Depends(get_db)):
    """
    POST /emails/generate
    Claude writes a personalized cold email per influencer.
    Saved with status 'Pending Approval'.
    """
    query = db.query(Influencer).filter(Influencer.email.isnot(None))

    if payload.influencer_ids:
        query = query.filter(Influencer.id.in_(payload.influencer_ids))
    else:
        # Default to influencers with email available who don't already have an outreach email
        subquery = db.query(OutreachEmail.influencer_id).subquery()
        query = query.filter(~Influencer.id.in_(subquery))

    targets = query.all()
    if not targets:
        raise HTTPException(status_code=404, detail="No eligible influencers with email found for generation.")

    generated_emails = []

    for inf in targets:
        brand = payload.brand or (inf.campaign_rel.brand if inf.campaign_rel else settings.DEFAULT_BRAND_NAME)
        sender_name = payload.sender_name or (inf.campaign_rel.sender_name if inf.campaign_rel else settings.DEFAULT_SENDER_NAME)
        offer = payload.offer or (inf.campaign_rel.offer_details if inf.campaign_rel else "Free product kit + 15% affiliate commission")
        summary = inf.profile_summary or f"{inf.name} creates content in {inf.niche or 'social media'}"

        email_data = claude_service.generate_cold_email(
            sender_name=sender_name,
            brand=brand,
            influencer_name=inf.name,
            summary=summary,
            offer=offer
        )

        email_record = OutreachEmail(
            influencer_id=inf.id,
            recipient_email=inf.email,
            subject=email_data["subject"],
            body=email_data["body"],
            email_type="initial",
            status="Pending Approval"
        )
        db.add(email_record)
        db.commit()
        db.refresh(email_record)
        generated_emails.append(email_record)

    return generated_emails


@router.post("/approve/{email_id}", response_model=OutreachEmailResponse)
def approve_email(
    email_id: int,
    payload: Optional[EmailUpdateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    POST /emails/approve/{id}
    Approve email and optionally update edited subject/body.
    """
    email_rec = db.query(OutreachEmail).filter(OutreachEmail.id == email_id).first()
    if not email_rec:
        raise HTTPException(status_code=404, detail="Email record not found.")

    if payload:
        if payload.subject:
            email_rec.subject = payload.subject
        if payload.body:
            email_rec.body = payload.body

    email_rec.status = "Approved"
    db.commit()
    db.refresh(email_rec)
    return email_rec


@router.post("/reject/{email_id}", response_model=OutreachEmailResponse)
def reject_email(email_id: int, db: Session = Depends(get_db)):
    """POST /emails/reject/{id}"""
    email_rec = db.query(OutreachEmail).filter(OutreachEmail.id == email_id).first()
    if not email_rec:
        raise HTTPException(status_code=404, detail="Email record not found.")

    email_rec.status = "Rejected"
    db.commit()
    db.refresh(email_rec)
    return email_rec


@router.post("/send")
def send_approved_emails(
    payload: Optional[SendEmailsRequest] = None,
    db: Session = Depends(get_db)
):
    """
    POST /emails/send
    Send via Gmail API ONLY after human approval.
    Enforces daily send limit and delay between sends.
    Stores threadId and messageId.
    """
    query = db.query(OutreachEmail).filter(OutreachEmail.status == "Approved")
    if payload and payload.email_ids:
        query = query.filter(OutreachEmail.id.in_(payload.email_ids))

    approved_list = query.all()
    if not approved_list:
        return {"message": "No approved emails waiting to be sent.", "sent_count": 0}

    sent_count = 0
    errors = []

    for email_item in approved_list:
        inf = email_item.influencer
        try:
            send_result = gmail_service.send_email(
                to_email=email_item.recipient_email,
                subject=email_item.subject,
                body_text=email_item.body,
                thread_id=email_item.gmail_thread_id or (inf.thread_id if inf else None),
                in_reply_to_message_id=email_item.gmail_message_id
            )

            # Update email record
            email_item.status = "Sent"
            email_item.gmail_message_id = send_result.get("message_id")
            email_item.gmail_thread_id = send_result.get("thread_id")
            email_item.sent_at = datetime.utcnow()
            email_item.error_message = None

            # Update influencer CRM tracking
            if inf:
                inf.status = LeadStatus.EMAIL_SENT
                inf.thread_id = send_result.get("thread_id")
                inf.last_email_date = datetime.utcnow()
                if email_item.email_type.startswith("followup"):
                    inf.followup_count += 1

                # Sync to Google Sheets CRM
                sheets_service.sync_influencer({
                    "username": inf.username,
                    "email": inf.email,
                    "status": inf.status,
                    "thread_id": inf.thread_id,
                    "last_email_date": inf.last_email_date,
                    "followup_count": inf.followup_count,
                    "notes": f"Sent {email_item.email_type} email."
                })

            db.commit()
            sent_count += 1
        except Exception as e:
            err_msg = str(e)
            logger.error("Failed to send email id=%s to %s: %s", email_item.id, email_item.recipient_email, err_msg)
            email_item.status = "Failed"
            email_item.error_message = err_msg
            db.commit()
            errors.append({"email_id": email_item.id, "error": err_msg})
            # If daily limit reached, break loop immediately
            if "Daily send limit" in err_msg:
                break

    return {
        "message": f"Sent {sent_count} emails successfully.",
        "sent_count": sent_count,
        "errors": errors
    }


@router.get("/queue", response_model=List[OutreachEmailResponse])
def list_email_queue(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get emails in the outreach queue."""
    query = db.query(OutreachEmail)
    if status and isinstance(status, str):
        query = query.filter(OutreachEmail.status == status)
    return query.order_by(OutreachEmail.created_at.desc()).all()


@router.get("/stats")
def get_send_stats():
    """Return daily send limit meter and current usage."""
    return gmail_service.get_daily_send_stats()
