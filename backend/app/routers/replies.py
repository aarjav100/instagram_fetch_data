import logging
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Influencer, InboundReply, LeadStatus
from app.schemas import InboundReplyResponse, ReplyActionRequest
from app.services.reply_service import process_inbound_message, poll_gmail_replies
from app.services.gmail_service import gmail_service

router = APIRouter(prefix="/replies", tags=["Reply Management"])
logger = logging.getLogger("replies_router")


class SimulateReplyRequest(BaseModel):
    influencer_id: int
    reply_text: str
    sender_email: Optional[str] = None


@router.get("", response_model=List[InboundReplyResponse])
def get_all_replies(db: Session = Depends(get_db)):
    """List all inbound replies classified by Claude with suggested next action and drafts."""
    return db.query(InboundReply).order_by(InboundReply.received_at.desc()).all()


@router.post("/poll")
def poll_threads_now(db: Session = Depends(get_db)):
    """Manually trigger reply polling for active threads."""
    count = poll_gmail_replies(db)
    return {"message": f"Polled threads. Processed {count} new replies.", "processed": count}


@router.post("/simulate", response_model=InboundReplyResponse)
def simulate_reply(payload: SimulateReplyRequest, db: Session = Depends(get_db)):
    """
    Simulate an inbound message from an influencer.
    Demonstrates Claude's classification, suggested action, and draft response.
    """
    influencer = db.query(Influencer).filter(Influencer.id == payload.influencer_id).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found.")

    sim_msg_id = f"sim_inbound_{datetime.utcnow().timestamp()}"
    sim_thread_id = influencer.thread_id or f"thread_{influencer.id}"
    sender_email = payload.sender_email or influencer.email or f"{influencer.username}@creator.com"

    reply_rec = process_inbound_message(
        db=db,
        influencer=influencer,
        message_id=sim_msg_id,
        thread_id=sim_thread_id,
        sender_email=sender_email,
        snippet=payload.reply_text[:120],
        body=payload.reply_text
    )
    return reply_rec


@router.post("/approve/{reply_id}", response_model=InboundReplyResponse)
def approve_reply_draft(
    reply_id: int,
    payload: Optional[ReplyActionRequest] = None,
    db: Session = Depends(get_db)
):
    """Approve or edit AI draft reply."""
    reply_rec = db.query(InboundReply).filter(InboundReply.id == reply_id).first()
    if not reply_rec:
        raise HTTPException(status_code=404, detail="Reply record not found.")

    if payload:
        if payload.draft_reply is not None:
            reply_rec.draft_reply = payload.draft_reply
        if payload.status:
            reply_rec.draft_status = payload.status
        else:
            reply_rec.draft_status = "Approved"
    else:
        reply_rec.draft_status = "Approved"

    db.commit()
    db.refresh(reply_rec)
    return reply_rec


@router.post("/send/{reply_id}")
def send_reply_draft(reply_id: int, db: Session = Depends(get_db)):
    """Send approved draft reply in the same Gmail thread."""
    reply_rec = db.query(InboundReply).filter(InboundReply.id == reply_id).first()
    if not reply_rec:
        raise HTTPException(status_code=404, detail="Reply record not found.")

    if not reply_rec.draft_reply:
        raise HTTPException(status_code=400, detail="No draft reply exists to send.")

    # Send in the same thread
    try:
        subject = "Re: Collaboration with " + (reply_rec.influencer.name if reply_rec.influencer else "Creator")
        result = gmail_service.send_email(
            to_email=reply_rec.sender_email,
            subject=subject,
            body_text=reply_rec.draft_reply,
            thread_id=reply_rec.gmail_thread_id,
            in_reply_to_message_id=reply_rec.gmail_message_id
        )

        reply_rec.draft_status = "Sent"
        reply_rec.draft_sent_at = datetime.utcnow()

        if reply_rec.category == "interested":
            reply_rec.influencer.status = LeadStatus.COLLABORATION_CONFIRMED

        db.commit()
        return {"message": "Draft reply sent successfully.", "result": result}
    except Exception as e:
        logger.error("Failed to send draft reply: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
