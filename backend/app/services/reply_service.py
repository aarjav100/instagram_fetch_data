import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Influencer, InboundReply, LeadStatus
from app.services.claude_service import claude_service
from app.services.gmail_service import gmail_service
from app.services.sheets_service import sheets_service

logger = logging.getLogger("reply_service")


def map_category_to_status(category: str) -> str:
    cat = (category or "").lower().strip()
    if cat == "interested":
        return LeadStatus.INTERESTED
    elif cat == "not_interested":
        return LeadStatus.NOT_INTERESTED
    elif cat == "opt_out":
        return LeadStatus.OPTED_OUT
    elif cat in ["pricing_enquiry", "collaboration_request"]:
        return LeadStatus.REPLIED
    else:
        return LeadStatus.REPLIED


def process_inbound_message(
    db: Session,
    influencer: Influencer,
    message_id: str,
    thread_id: str,
    sender_email: str,
    snippet: str,
    body: str
) -> Optional[InboundReply]:
    """
    Classify an incoming email reply with Claude, save inbound reply record,
    and update influencer and Google Sheets status.
    """
    # Check if message is already recorded
    existing = db.query(InboundReply).filter(InboundReply.gmail_message_id == message_id).first()
    if existing:
        return existing

    # Classify with Claude
    classification = claude_service.classify_reply(body or snippet)
    category = classification.get("category", "other")
    suggested_action = classification.get("suggested_next_action", "")
    draft_reply = classification.get("draft_reply", "")

    new_reply = InboundReply(
        influencer_id=influencer.id,
        gmail_message_id=message_id,
        gmail_thread_id=thread_id,
        sender_email=sender_email,
        snippet=snippet,
        body=body,
        category=category,
        suggested_next_action=suggested_action,
        draft_reply=draft_reply,
        draft_status="Pending Approval",
        received_at=datetime.utcnow()
    )
    db.add(new_reply)

    # Update influencer status
    new_status = map_category_to_status(category)
    influencer.status = new_status
    influencer.notes = f"Reply classified as '{category}'. Suggested: {suggested_action}"
    db.commit()
    db.refresh(new_reply)

    # Sync status to Google Sheets
    sheets_service.sync_influencer({
        "username": influencer.username,
        "email": influencer.email,
        "status": influencer.status,
        "thread_id": influencer.thread_id,
        "notes": influencer.notes
    })

    logger.info("Processed reply from %s: category=%s, new status=%s", sender_email, category, new_status)
    return new_reply


def poll_gmail_replies(db: Session) -> int:
    """
    Poll all active influencer threads for new incoming messages.
    """
    influencers_with_threads = db.query(Influencer).filter(
        Influencer.thread_id.isnot(None),
        Influencer.status.in_([LeadStatus.EMAIL_SENT, LeadStatus.FOLLOW_UP_DUE, LeadStatus.REPLIED])
    ).all()

    processed_count = 0
    for inf in influencers_with_threads:
        try:
            inbound_msgs = gmail_service.fetch_thread_replies(inf.thread_id)
            for msg in inbound_msgs:
                reply = process_inbound_message(
                    db=db,
                    influencer=inf,
                    message_id=msg["message_id"],
                    thread_id=msg["thread_id"],
                    sender_email=msg["sender_email"],
                    snippet=msg.get("snippet", ""),
                    body=msg.get("body", "")
                )
                if reply:
                    processed_count += 1
        except Exception as e:
            logger.error("Error polling thread %s for influencer %s: %s", inf.thread_id, inf.username, e)

    return processed_count
