import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Influencer, OutreachEmail, LeadStatus
from app.services.claude_service import claude_service
from app.services.sheets_service import sheets_service
from app.config import settings

logger = logging.getLogger("followup_service")

STOPPED_STATUSES = [
    LeadStatus.REPLIED,
    LeadStatus.INTERESTED,
    LeadStatus.NOT_INTERESTED,
    LeadStatus.COLLABORATION_CONFIRMED,
    LeadStatus.OPTED_OUT
]


def evaluate_due_followups(db: Session) -> List[Dict[str, Any]]:
    """
    Find leads where initial email was sent and no reply has been received:
    - Step 1: 3-5 days after initial email -> Follow-up 1
    - Step 2: 5-7 days after Follow-up 1 -> Follow-up 2 (max 2)
    Stops automatically if Replied, Not Interested, or Opted Out.
    """
    now = datetime.utcnow()
    leads = db.query(Influencer).filter(
        Influencer.status.in_([LeadStatus.EMAIL_SENT, LeadStatus.FOLLOW_UP_DUE]),
        Influencer.followup_count < 2
    ).all()

    due_list = []
    for lead in leads:
        if lead.status in STOPPED_STATUSES:
            continue

        if not lead.last_email_date or not lead.email:
            continue

        delta = now - lead.last_email_date
        days = delta.days

        # Step 1: Follow-up 1 (after 3 days)
        if lead.followup_count == 0 and days >= 3:
            # Fetch original email subject
            original_email = db.query(OutreachEmail).filter(
                OutreachEmail.influencer_id == lead.id,
                OutreachEmail.email_type == "initial"
            ).first()
            orig_subject = original_email.subject if original_email else f"Partnership with {settings.DEFAULT_BRAND_NAME}"

            due_list.append({
                "influencer_id": lead.id,
                "name": lead.name,
                "username": lead.username,
                "email": lead.email,
                "status": lead.status,
                "last_email_date": lead.last_email_date,
                "followup_count": lead.followup_count,
                "thread_id": lead.thread_id,
                "next_step": "Follow-up 1",
                "days_since_last_email": days,
                "suggested_subject": f"Re: {orig_subject.lstrip('Re: ')}",
            })

        # Step 2: Follow-up 2 (after 5 days since follow-up 1)
        elif lead.followup_count == 1 and days >= 5:
            original_email = db.query(OutreachEmail).filter(
                OutreachEmail.influencer_id == lead.id
            ).first()
            orig_subject = original_email.subject if original_email else f"Partnership with {settings.DEFAULT_BRAND_NAME}"

            due_list.append({
                "influencer_id": lead.id,
                "name": lead.name,
                "username": lead.username,
                "email": lead.email,
                "status": lead.status,
                "last_email_date": lead.last_email_date,
                "followup_count": lead.followup_count,
                "thread_id": lead.thread_id,
                "next_step": "Follow-up 2",
                "days_since_last_email": days,
                "suggested_subject": f"Re: {orig_subject.lstrip('Re: ')}",
            })

    return due_list


def generate_followup_email(db: Session, influencer_id: int) -> OutreachEmail:
    """Generate follow-up email draft using Claude and save as Pending Approval."""
    lead = db.query(Influencer).filter(Influencer.id == influencer_id).first()
    if not lead or not lead.email:
        raise ValueError("Influencer not found or has no email")

    if lead.status in STOPPED_STATUSES:
        raise ValueError(f"Cannot follow up: Lead status is {lead.status}")

    step = lead.followup_count + 1
    if step > 2:
        raise ValueError("Maximum 2 follow-ups already reached.")

    # Get campaign details or defaults
    brand = settings.DEFAULT_BRAND_NAME
    offer = "Product kit + commission"
    sender = settings.DEFAULT_SENDER_NAME

    if lead.campaign_rel:
        brand = lead.campaign_rel.brand or brand
        offer = lead.campaign_rel.offer_details or offer
        sender = lead.campaign_rel.sender_name or sender

    original_email = db.query(OutreachEmail).filter(
        OutreachEmail.influencer_id == lead.id
    ).first()
    orig_subject = original_email.subject if original_email else f"Partnership with {brand}"

    email_data = claude_service.generate_followup(
        step=step,
        sender_name=sender,
        brand=brand,
        influencer_name=lead.name,
        offer=offer,
        original_subject=orig_subject
    )

    outreach = OutreachEmail(
        influencer_id=lead.id,
        recipient_email=lead.email,
        subject=email_data["subject"],
        body=email_data["body"],
        email_type=f"followup_{step}",
        status="Pending Approval",
        gmail_thread_id=lead.thread_id
    )
    db.add(outreach)

    lead.status = LeadStatus.FOLLOW_UP_DUE
    db.commit()
    db.refresh(outreach)

    # Sync to sheets
    sheets_service.sync_influencer({
        "username": lead.username,
        "email": lead.email,
        "status": lead.status,
        "followup_count": lead.followup_count,
        "notes": f"Generated follow-up {step} draft."
    })

    return outreach
