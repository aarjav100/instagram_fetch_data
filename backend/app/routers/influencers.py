from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Influencer, LeadStatus
from app.schemas import InfluencerResponse
from app.services.sheets_service import sheets_service

router = APIRouter(prefix="/influencers", tags=["Influencers"])


@router.get("", response_model=List[InfluencerResponse])
def get_influencers(
    status: Optional[str] = None,
    niche: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    min_score: Optional[int] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    sort_by: Optional[str] = "score_desc",
    db: Session = Depends(get_db)
):
    """Retrieve all influencers with robust filtering and sorting."""
    query = db.query(Influencer)

    if status and isinstance(status, str):
        query = query.filter(Influencer.status == status)
    if niche and isinstance(niche, str):
        query = query.filter(Influencer.niche.ilike(f"%{niche}%"))
    if priority and isinstance(priority, str):
        query = query.filter(Influencer.priority == priority)
    if min_score is not None and isinstance(min_score, (int, float)):
        query = query.filter(Influencer.relevance_score >= min_score)
    if min_followers is not None and isinstance(min_followers, (int, float)):
        query = query.filter(Influencer.followers >= min_followers)
    if max_followers is not None and isinstance(max_followers, (int, float)):
        query = query.filter(Influencer.followers <= max_followers)
    if search and isinstance(search, str):
        search_pattern = f"%{search}%"
        query = query.filter(
            (Influencer.name.ilike(search_pattern)) |
            (Influencer.username.ilike(search_pattern)) |
            (Influencer.email.ilike(search_pattern)) |
            (Influencer.bio.ilike(search_pattern)) |
            (Influencer.profile_summary.ilike(search_pattern))
        )


    if sort_by == "score_desc":
        query = query.order_by(Influencer.relevance_score.desc())
    elif sort_by == "score_asc":
        query = query.order_by(Influencer.relevance_score.asc())
    elif sort_by == "followers_desc":
        query = query.order_by(Influencer.followers.desc())
    elif sort_by == "followers_asc":
        query = query.order_by(Influencer.followers.asc())
    elif sort_by == "recent":
        query = query.order_by(Influencer.created_at.desc())
    else:
        query = query.order_by(Influencer.relevance_score.desc())

    return query.all()


@router.get("/{influencer_id}", response_model=InfluencerResponse)
def get_influencer_by_id(influencer_id: int, db: Session = Depends(get_db)):
    """Get single influencer details."""
    inf = db.query(Influencer).filter(Influencer.id == influencer_id).first()
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found.")
    return inf


@router.patch("/{influencer_id}", response_model=InfluencerResponse)
def update_influencer(
    influencer_id: int,
    status: Optional[str] = None,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update influencer status, email or notes."""
    inf = db.query(Influencer).filter(Influencer.id == influencer_id).first()
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found.")

    if status:
        inf.status = status
    if email is not None:
        inf.email = email.strip().lower() if email.strip() else None
        if inf.email and inf.status == LeadStatus.NEW_LEAD:
            inf.status = LeadStatus.EMAIL_AVAILABLE
    if notes is not None:
        inf.notes = notes

    db.commit()
    db.refresh(inf)

    # Sync to Google Sheets CRM
    sheets_service.sync_influencer({
        "username": inf.username,
        "email": inf.email or "",
        "status": inf.status,
        "notes": inf.notes or ""
    })

    return inf


@router.delete("/{influencer_id}")
def delete_influencer(influencer_id: int, db: Session = Depends(get_db)):
    """Delete an influencer from the CRM."""
    inf = db.query(Influencer).filter(Influencer.id == influencer_id).first()
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found.")
    db.delete(inf)
    db.commit()
    return {"message": "Influencer deleted successfully."}
