from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    brand: str = Field(..., description="Brand name running the campaign")
    campaign: str = Field(..., description="Campaign name or objective")
    niche: Optional[str] = Field(None, description="Target niche, e.g. Fitness, Beauty, Tech")
    keywords: Optional[str] = Field(None, description="Keywords to match, comma separated")
    location: Optional[str] = Field(None, description="Target geographical location")
    min_followers: Optional[int] = Field(0, description="Minimum follower count")
    max_followers: Optional[int] = Field(10000000, description="Maximum follower count")
    usernames: List[str] = Field(default_factory=list, description="List of Instagram usernames to research")
    offer_details: Optional[str] = Field(
        "Free exclusive product suite + 15% revenue share commission on branded code",
        description="Collaboration offer details"
    )
    sender_name: Optional[str] = Field("Partnerships Lead", description="Outreach sender name")


class InfluencerBase(BaseModel):
    name: str
    username: str
    profile_link: Optional[str] = None
    niche: Optional[str] = None
    followers: int = 0
    email: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    category: Optional[str] = None
    profile_pic_url: Optional[str] = None
    relevance_score: int = 0
    profile_summary: Optional[str] = None
    suitability_reason: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "New Lead"
    thread_id: Optional[str] = None
    last_email_date: Optional[datetime] = None
    followup_count: int = 0
    notes: Optional[str] = None


class InfluencerResponse(InfluencerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailGenerateRequest(BaseModel):
    influencer_ids: Optional[List[int]] = None
    campaign_id: Optional[int] = None
    brand: Optional[str] = None
    sender_name: Optional[str] = None
    offer: Optional[str] = None


class EmailUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None  # Approved, Rejected, Pending Approval


class OutreachEmailResponse(BaseModel):
    id: int
    influencer_id: int
    recipient_email: str
    subject: str
    body: str
    email_type: str
    status: str
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None
    influencer: Optional[InfluencerResponse] = None

    class Config:
        from_attributes = True


class SendEmailsRequest(BaseModel):
    email_ids: Optional[List[int]] = None


class InboundReplyResponse(BaseModel):
    id: int
    influencer_id: int
    gmail_message_id: str
    gmail_thread_id: str
    sender_email: str
    snippet: Optional[str] = None
    body: str
    received_at: datetime
    category: Optional[str] = None
    suggested_next_action: Optional[str] = None
    draft_reply: Optional[str] = None
    draft_status: str
    draft_sent_at: Optional[datetime] = None
    influencer: Optional[InfluencerResponse] = None

    class Config:
        from_attributes = True


class ReplyActionRequest(BaseModel):
    draft_reply: Optional[str] = None
    status: Optional[str] = None  # Approved, Rejected, Sent


class FollowUpItemResponse(BaseModel):
    influencer_id: int
    name: str
    username: str
    email: str
    status: str
    last_email_date: Optional[datetime] = None
    followup_count: int
    thread_id: Optional[str] = None
    next_step: str  # "Follow-up 1" or "Follow-up 2" or "Max Reached"
    days_since_last_email: Optional[int] = None
    suggested_subject: str
    suggested_body: Optional[str] = None


class DashboardStats(BaseModel):
    total_leads: int
    emails_sent: int
    replies: int
    interested: int
    collaborations_confirmed: int
    daily_sent_count: int
    daily_limit: int
    status_breakdown: Dict[str, int]
    pipeline: List[Dict[str, Any]]
