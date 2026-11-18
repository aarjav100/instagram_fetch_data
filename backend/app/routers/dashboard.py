from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Influencer, OutreachEmail, InboundReply, DailySendCounter, LeadStatus
from app.schemas import DashboardStats
from app.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Calculate and return all CRM metrics, pipeline distribution, and send capacity."""
    total_leads = db.query(Influencer).count()

    emails_sent = db.query(OutreachEmail).filter(OutreachEmail.status == "Sent").count()
    replies = db.query(InboundReply).count()

    interested = db.query(Influencer).filter(
        Influencer.status.in_([LeadStatus.INTERESTED, LeadStatus.COLLABORATION_CONFIRMED])
    ).count()

    collabs_confirmed = db.query(Influencer).filter(
        Influencer.status == LeadStatus.COLLABORATION_CONFIRMED
    ).count()

    today_str = date.today().isoformat()
    counter = db.query(DailySendCounter).filter(DailySendCounter.send_date == today_str).first()
    daily_sent = counter.count if counter else 0

    # Status breakdown
    counts_by_status = dict(
        db.query(Influencer.status, func.count(Influencer.id))
        .group_by(Influencer.status)
        .all()
    )

    full_status_breakdown = {status: counts_by_status.get(status, 0) for status in LeadStatus.ALL}

    pipeline_stages = [
        {"stage": "New Leads", "count": full_status_breakdown.get(LeadStatus.NEW_LEAD, 0), "color": "#6366f1"},
        {"stage": "Email Available", "count": full_status_breakdown.get(LeadStatus.EMAIL_AVAILABLE, 0), "color": "#3b82f6"},
        {"stage": "Email Sent", "count": full_status_breakdown.get(LeadStatus.EMAIL_SENT, 0), "color": "#0ea5e9"},
        {"stage": "Follow-up Due", "count": full_status_breakdown.get(LeadStatus.FOLLOW_UP_DUE, 0), "color": "#f59e0b"},
        {"stage": "Replied", "count": full_status_breakdown.get(LeadStatus.REPLIED, 0), "color": "#8b5cf6"},
        {"stage": "Interested", "count": full_status_breakdown.get(LeadStatus.INTERESTED, 0), "color": "#10b981"},
        {"stage": "Collab Confirmed", "count": full_status_breakdown.get(LeadStatus.COLLABORATION_CONFIRMED, 0), "color": "#059669"},
        {"stage": "Not Interested", "count": full_status_breakdown.get(LeadStatus.NOT_INTERESTED, 0), "color": "#9ca3af"},
        {"stage": "Opted Out", "count": full_status_breakdown.get(LeadStatus.OPTED_OUT, 0), "color": "#ef4444"},
    ]

    return DashboardStats(
        total_leads=total_leads,
        emails_sent=emails_sent,
        replies=replies,
        interested=interested,
        collaborations_confirmed=collabs_confirmed,
        daily_sent_count=daily_sent,
        daily_limit=settings.DAILY_SEND_LIMIT,
        status_breakdown=full_status_breakdown,
        pipeline=pipeline_stages
    )
