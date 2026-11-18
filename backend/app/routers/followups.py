import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import FollowUpItemResponse, OutreachEmailResponse
from app.services.followup_service import evaluate_due_followups, generate_followup_email

router = APIRouter(prefix="/followups", tags=["Follow-ups"])
logger = logging.getLogger("followups_router")


@router.get("/due", response_model=List[FollowUpItemResponse])
def get_due_followups(db: Session = Depends(get_db)):
    """
    Find 'Email Sent' leads with no reply after 3-5 days (Follow-up 1)
    or after 5-7 more days (Follow-up 2, max 2).
    """
    return evaluate_due_followups(db)


@router.post("/generate/{influencer_id}", response_model=OutreachEmailResponse)
def trigger_generate_followup(influencer_id: int, db: Session = Depends(get_db)):
    """Generate follow-up draft for a specific influencer and save to approval queue."""
    try:
        outreach = generate_followup_email(db, influencer_id)
        return outreach
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error generating follow-up: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-check")
def trigger_all_due_followups(db: Session = Depends(get_db)):
    """Evaluate and generate drafts for all leads currently due for follow-up."""
    due = evaluate_due_followups(db)
    generated = []
    for item in due:
        try:
            outreach = generate_followup_email(db, item["influencer_id"])
            generated.append(outreach.id)
        except Exception as e:
            logger.error("Failed to generate follow-up for %s: %s", item["username"], e)

    return {
        "message": f"Processed {len(due)} due leads. Created {len(generated)} follow-up drafts.",
        "created_email_ids": generated
    }
