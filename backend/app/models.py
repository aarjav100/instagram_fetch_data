from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class LeadStatus:
    NEW_LEAD = "New Lead"
    EMAIL_AVAILABLE = "Email Available"
    EMAIL_SENT = "Email Sent"
    FOLLOW_UP_DUE = "Follow-up Due"
    REPLIED = "Replied"
    INTERESTED = "Interested"
    NOT_INTERESTED = "Not Interested"
    COLLABORATION_CONFIRMED = "Collaboration Confirmed"
    OPTED_OUT = "Opted Out"

    ALL = [
        NEW_LEAD,
        EMAIL_AVAILABLE,
        EMAIL_SENT,
        FOLLOW_UP_DUE,
        REPLIED,
        INTERESTED,
        NOT_INTERESTED,
        COLLABORATION_CONFIRMED,
        OPTED_OUT,
    ]


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False)
    campaign = Column(String(255), nullable=False)
    niche = Column(String(255), nullable=True)
    keywords = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    min_followers = Column(Integer, default=0)
    max_followers = Column(Integer, default=10000000)
    offer_details = Column(Text, nullable=True)
    sender_name = Column(String(255), default="Partnership Manager")
    created_at = Column(DateTime, default=datetime.utcnow)

    influencers = relationship("Influencer", back_populates="campaign_rel", cascade="all, delete-orphan")


class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    profile_link = Column(String(500), nullable=True)
    niche = Column(String(255), nullable=True)
    followers = Column(Integer, default=0)
    email = Column(String(255), index=True, nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    profile_pic_url = Column(String(1000), nullable=True)

    # AI Analysis (Claude)
    relevance_score = Column(Integer, default=0)
    profile_summary = Column(Text, nullable=True)
    suitability_reason = Column(Text, nullable=True)
    priority = Column(String(50), default="Medium")  # High, Medium, Low

    # CRM tracking & Sheet fields
    status = Column(String(100), default=LeadStatus.NEW_LEAD, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    last_email_date = Column(DateTime, nullable=True)
    followup_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    campaign_rel = relationship("Campaign", back_populates="influencers")

    emails = relationship("OutreachEmail", back_populates="influencer", cascade="all, delete-orphan")
    replies = relationship("InboundReply", back_populates="influencer", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"

    id = Column(Integer, primary_key=True, index=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    email_type = Column(String(50), default="initial")  # initial, followup_1, followup_2
    status = Column(String(50), default="Pending Approval", index=True)  # Pending Approval, Approved, Rejected, Sent, Failed

    gmail_message_id = Column(String(255), nullable=True)
    gmail_thread_id = Column(String(255), nullable=True, index=True)

    scheduled_for = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    influencer = relationship("Influencer", back_populates="emails")


class InboundReply(Base):
    __tablename__ = "inbound_replies"

    id = Column(Integer, primary_key=True, index=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    gmail_message_id = Column(String(255), unique=True, index=True, nullable=False)
    gmail_thread_id = Column(String(255), index=True, nullable=False)
    sender_email = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    # Claude classification
    # interested | not_interested | pricing_enquiry | collaboration_request | opt_out | other
    category = Column(String(100), nullable=True)
    suggested_next_action = Column(Text, nullable=True)
    draft_reply = Column(Text, nullable=True)
    draft_status = Column(String(50), default="Pending Approval")  # Pending Approval, Approved, Sent, Rejected
    draft_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    influencer = relationship("Influencer", back_populates="replies")


class DailySendCounter(Base):
    __tablename__ = "daily_send_counters"

    id = Column(Integer, primary_key=True, index=True)
    send_date = Column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    count = Column(Integer, default=0)
