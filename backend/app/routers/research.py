import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Influencer, Campaign, LeadStatus
from app.schemas import ResearchRequest, InfluencerResponse
from app.services.instagram_service import instagram_service
from app.services.claude_service import claude_service
from app.services.sheets_service import sheets_service

router = APIRouter(prefix="/research", tags=["Influencer Research"])
logger = logging.getLogger("research_router")


@router.post("", response_model=List[InfluencerResponse])
def run_research(payload: ResearchRequest, db: Session = Depends(get_db)):
    """
    POST /research
    1. Fetch public profile via Instagram Graph API Business Discovery.
    2. Extract public business email from bio via regex.
    3. Call Claude for AI Filtering (niche, relevance_score, suitability_reason, profile_summary, priority).
    4. De-duplicate by username and email.
    5. Save results to DB and Google Sheets CRM, sorted by score.
    """
    if not payload.usernames:
        raise HTTPException(status_code=400, detail="At least one Instagram username is required.")

    # Create campaign record
    campaign = Campaign(
        brand=payload.brand,
        campaign=payload.campaign,
        niche=payload.niche,
        keywords=payload.keywords,
        location=payload.location,
        min_followers=payload.min_followers or 0,
        max_followers=payload.max_followers or 10000000,
        offer_details=payload.offer_details,
        sender_name=payload.sender_name
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    processed_influencers = []

    for username in payload.usernames:
        clean_user = username.strip().lstrip("@")
        if not clean_user:
            continue

        # 1. Fetch public Instagram data
        ig_data = instagram_service.fetch_user_business_discovery(clean_user)

        # Apply follower filters if configured
        followers = ig_data.get("followers", 0)
        if payload.min_followers and followers < payload.min_followers:
            logger.info("Skipping %s: followers %d below min %d", clean_user, followers, payload.min_followers)
            continue
        if payload.max_followers and followers > payload.max_followers:
            logger.info("Skipping %s: followers %d above max %d", clean_user, followers, payload.max_followers)
            continue

        # 2. Claude AI Filtering & Analysis
        ai_eval = claude_service.filter_influencer(
            brand=payload.brand,
            campaign=payload.campaign,
            influencer_data=ig_data
        )

        email = ig_data.get("email")
        initial_status = LeadStatus.EMAIL_AVAILABLE if email else LeadStatus.NEW_LEAD

        # 3. De-duplicate by username or email before inserting
        existing = db.query(Influencer).filter(
            (Influencer.username == clean_user) |
            ((Influencer.email != None) & (Influencer.email == email)) if email else (Influencer.username == clean_user)
        ).first()

        if existing:
            # Update existing record
            existing.name = ig_data.get("name", existing.name)
            existing.profile_link = ig_data.get("profile_link", existing.profile_link)
            existing.followers = followers
            existing.bio = ig_data.get("bio", existing.bio)
            existing.category = ig_data.get("category", existing.category)
            existing.profile_pic_url = ig_data.get("profile_pic_url", existing.profile_pic_url)
            if email and not existing.email:
                existing.email = email
                if existing.status == LeadStatus.NEW_LEAD:
                    existing.status = LeadStatus.EMAIL_AVAILABLE
            existing.niche = ai_eval.get("niche", existing.niche)
            existing.relevance_score = ai_eval.get("relevance_score", existing.relevance_score)
            existing.profile_summary = ai_eval.get("profile_summary", existing.profile_summary)
            existing.suitability_reason = ai_eval.get("suitability_reason", existing.suitability_reason)
            existing.priority = ai_eval.get("priority", existing.priority)
            existing.campaign_id = campaign.id
            db.commit()
            db.refresh(existing)
            influencer_obj = existing
        else:
            influencer_obj = Influencer(
                name=ig_data.get("name") or clean_user.capitalize(),
                username=clean_user,
                profile_link=ig_data.get("profile_link", f"https://instagram.com/{clean_user}"),
                followers=followers,
                bio=ig_data.get("bio", ""),
                category=ig_data.get("category", "Creator"),
                profile_pic_url=ig_data.get("profile_pic_url"),
                email=email,
                niche=ai_eval.get("niche", payload.niche or "Creator"),
                location=payload.location,
                relevance_score=ai_eval.get("relevance_score", 70),
                profile_summary=ai_eval.get("profile_summary", ""),
                suitability_reason=ai_eval.get("suitability_reason", ""),
                priority=ai_eval.get("priority", "Medium"),
                status=initial_status,
                campaign_id=campaign.id
            )
            db.add(influencer_obj)
            db.commit()
            db.refresh(influencer_obj)

        # 4. Sync to Google Sheets CRM (de-duplicated)
        sheets_service.sync_influencer({
            "name": influencer_obj.name,
            "username": influencer_obj.username,
            "profile_link": influencer_obj.profile_link,
            "niche": influencer_obj.niche,
            "followers": influencer_obj.followers,
            "email": influencer_obj.email or "",
            "location": influencer_obj.location or "",
            "profile_summary": influencer_obj.profile_summary or "",
            "relevance_score": influencer_obj.relevance_score,
            "status": influencer_obj.status,
            "thread_id": influencer_obj.thread_id or "",
            "last_email_date": influencer_obj.last_email_date or "",
            "followup_count": influencer_obj.followup_count,
            "notes": influencer_obj.suitability_reason or ""
        })

        processed_influencers.append(influencer_obj)

    # Sort results by relevance score descending
    processed_influencers.sort(key=lambda x: x.relevance_score, reverse=True)
    return processed_influencers


@router.post("/csv", response_model=List[InfluencerResponse])
async def upload_csv_research(
    file: UploadFile = File(...),
    brand: str = Form("Nova Brand"),
    campaign: str = Form("Creator Campaign"),
    db: Session = Depends(get_db)
):
    """
    Fallback CSV importer. Parses creator rows, evaluates with Claude,
    de-duplicates, and syncs to CRM.
    """
    contents = await file.read()
    records = instagram_service.parse_csv_data(contents)
    if not records:
        raise HTTPException(status_code=400, detail="No valid creator rows found in CSV.")

    processed = []
    for item in records:
        username = item["username"]
        ai_eval = claude_service.filter_influencer(
            brand=brand,
            campaign=campaign,
            influencer_data=item
        )

        email = item.get("email")
        initial_status = LeadStatus.EMAIL_AVAILABLE if email else LeadStatus.NEW_LEAD

        existing = db.query(Influencer).filter(
            (Influencer.username == username) |
            ((Influencer.email != None) & (Influencer.email == email)) if email else (Influencer.username == username)
        ).first()

        if existing:
            existing.followers = item.get("followers", existing.followers)
            existing.bio = item.get("bio", existing.bio)
            if email and not existing.email:
                existing.email = email
            existing.relevance_score = ai_eval.get("relevance_score", existing.relevance_score)
            existing.profile_summary = ai_eval.get("profile_summary", existing.profile_summary)
            existing.suitability_reason = ai_eval.get("suitability_reason", existing.suitability_reason)
            existing.priority = ai_eval.get("priority", existing.priority)
            db.commit()
            db.refresh(existing)
            inf_obj = existing
        else:
            inf_obj = Influencer(
                name=item.get("name", username.capitalize()),
                username=username,
                profile_link=item.get("profile_link", f"https://instagram.com/{username}"),
                followers=item.get("followers", 0),
                bio=item.get("bio", ""),
                category=item.get("category", "Creator"),
                email=email,
                niche=ai_eval.get("niche", item.get("niche", "General")),
                location=item.get("location", ""),
                relevance_score=ai_eval.get("relevance_score", 70),
                profile_summary=ai_eval.get("profile_summary", ""),
                suitability_reason=ai_eval.get("suitability_reason", ""),
                priority=ai_eval.get("priority", "Medium"),
                status=initial_status
            )
            db.add(inf_obj)
            db.commit()
            db.refresh(inf_obj)

        sheets_service.sync_influencer({
            "name": inf_obj.name,
            "username": inf_obj.username,
            "profile_link": inf_obj.profile_link,
            "niche": inf_obj.niche,
            "followers": inf_obj.followers,
            "email": inf_obj.email or "",
            "location": inf_obj.location or "",
            "profile_summary": inf_obj.profile_summary or "",
            "relevance_score": inf_obj.relevance_score,
            "status": inf_obj.status,
            "thread_id": inf_obj.thread_id or "",
            "last_email_date": inf_obj.last_email_date or "",
            "followup_count": inf_obj.followup_count,
            "notes": inf_obj.suitability_reason or ""
        })
        processed.append(inf_obj)

    processed.sort(key=lambda x: x.relevance_score, reverse=True)
    return processed
