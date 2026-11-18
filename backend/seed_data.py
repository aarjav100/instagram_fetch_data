"""
Seed database with realistic sample influencer pipeline data for instant verification and dashboard preview.
"""
from datetime import datetime, timedelta
from app.database import engine, SessionLocal, Base
from app.models import Influencer, Campaign, OutreachEmail, InboundReply, LeadStatus, DailySendCounter

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Influencer).count() > 0:
        print("Database already contains records. Skipping seed.")
        db.close()
        return

    print("Seeding sample campaign and influencer CRM records...")

    campaign = Campaign(
        brand="Aura Glow Skincare",
        campaign="Summer Hydration Glow Launch",
        niche="Clean Beauty & Skincare",
        keywords="clean beauty, glass skin, hydration, cruelty-free",
        location="United States",
        min_followers=10000,
        max_followers=250000,
        offer_details="Free Summer Glow Set ($180 value) + $350 flat fee + 15% recurring affiliate code",
        sender_name="Alex Rivera - Head of Partnerships"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    sample_creators = [
        {
            "name": "Elena Rostova",
            "username": "elena_glow",
            "profile_link": "https://instagram.com/elena_glow",
            "followers": 84200,
            "email": "collab.elena@gmail.com",
            "niche": "Clean Skincare & Wellness",
            "location": "Los Angeles, CA",
            "bio": "Esthetician & skincare obsessive ✨ Honest reviews & barrier repair rituals. Business: collab.elena@gmail.com",
            "category": "Beauty & Skincare",
            "profile_pic_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 94,
            "profile_summary": "Licensed aesthetician creating evidence-based barrier repair skincare routines with exceptionally high organic engagement.",
            "suitability_reason": "Direct audience alignment for Summer Hydration campaign with professional credibility.",
            "priority": "High",
            "status": LeadStatus.COLLABORATION_CONFIRMED,
            "thread_id": "thread_elena_001",
            "last_email_date": datetime.utcnow() - timedelta(days=2),
            "followup_count": 0,
            "notes": "Signed agreement. Product package shipped."
        },
        {
            "name": "Marcus Vance",
            "username": "marcus_fitglow",
            "profile_link": "https://instagram.com/marcus_fitglow",
            "followers": 142000,
            "email": "partnerships@marcusvance.co",
            "niche": "Fitness & Men's Grooming",
            "location": "Austin, TX",
            "bio": "Daily fitness habits + minimal skincare for active men. Inquiries: partnerships@marcusvance.co",
            "category": "Health & Grooming",
            "profile_pic_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 88,
            "profile_summary": "Male fitness & active lifestyle creator promoting morning hydration and daily SPF.",
            "suitability_reason": "High male demo crossover seeking straightforward hydration solutions.",
            "priority": "High",
            "status": LeadStatus.INTERESTED,
            "thread_id": "thread_marcus_002",
            "last_email_date": datetime.utcnow() - timedelta(days=1),
            "followup_count": 0,
            "notes": "Requested ingredient list and delivery address confirmation."
        },
        {
            "name": "Sophia Lin",
            "username": "sophia_lin_living",
            "profile_link": "https://instagram.com/sophia_lin_living",
            "followers": 52100,
            "email": "sophia.mgmt@creatorlabs.io",
            "niche": "Mindful Living & Clean Beauty",
            "location": "New York, NY",
            "bio": "Sustainable morning routines & slow beauty. Collabs: sophia.mgmt@creatorlabs.io",
            "category": "Lifestyle",
            "profile_pic_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 91,
            "profile_summary": "Aesthetic lifestyle creator focusing on minimalist clean routines with dedicated community discussions.",
            "suitability_reason": "Matches our cruelty-free sustainable packaging angle seamlessly.",
            "priority": "High",
            "status": LeadStatus.FOLLOW_UP_DUE,
            "thread_id": "thread_sophia_003",
            "last_email_date": datetime.utcnow() - timedelta(days=4),
            "followup_count": 0,
            "notes": "Initial email sent 4 days ago. Ready for Follow-up 1."
        },
        {
            "name": "Chloe & Liam",
            "username": "chloeliam_duo",
            "profile_link": "https://instagram.com/chloeliam_duo",
            "followers": 198000,
            "email": "contact@chloeandliam.com",
            "niche": "Couples Travel & Skincare",
            "location": "Miami, FL",
            "bio": "Chasing sunsets & keeping skin hydrated across continents ✈️ Business: contact@chloeandliam.com",
            "category": "Travel & Lifestyle",
            "profile_pic_url": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 79,
            "profile_summary": "Duo travel vloggers frequently sharing travel-friendly grooming and hydration essentials.",
            "suitability_reason": "Good for showcasing our travel-size serum packs.",
            "priority": "Medium",
            "status": LeadStatus.EMAIL_SENT,
            "thread_id": "thread_chloe_004",
            "last_email_date": datetime.utcnow() - timedelta(days=1),
            "followup_count": 0,
            "notes": "Cold email dispatched. Awaiting response."
        },
        {
            "name": "Maya Patel",
            "username": "mayaskinroutine",
            "profile_link": "https://instagram.com/mayaskinroutine",
            "followers": 38500,
            "email": "maya@mayapatel.me",
            "niche": "Dermatology Student & Skincare",
            "location": "Chicago, IL",
            "bio": "Med student breaking down skincare ingredients. Science over hype. PR/Collabs: maya@mayapatel.me",
            "category": "Beauty Education",
            "profile_pic_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 96,
            "profile_summary": "Dermatology medical student providing scientific breakdowns of hyaluronic acid and barrier ceramides.",
            "suitability_reason": "Top tier scientific credibility for hydration launch.",
            "priority": "High",
            "status": LeadStatus.EMAIL_AVAILABLE,
            "thread_id": None,
            "last_email_date": None,
            "followup_count": 0,
            "notes": "Generated high relevance score. Email draft queued."
        },
        {
            "name": "Zackary Taylor",
            "username": "zack_streetstyle",
            "profile_link": "https://instagram.com/zack_streetstyle",
            "followers": 61000,
            "email": "zack.collabs@streetwear.net",
            "niche": "Urban Fashion & Streetwear",
            "location": "Toronto, ON",
            "bio": "Vintage archives & streetwear culture. Collabs: zack.collabs@streetwear.net",
            "category": "Fashion",
            "profile_pic_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
            "relevance_score": 58,
            "profile_summary": "Streetwear fashion archivist focusing on vintage denim and sneaker culture.",
            "suitability_reason": "Low direct alignment with clean hydration skincare focus.",
            "priority": "Low",
            "status": LeadStatus.NEW_LEAD,
            "thread_id": None,
            "last_email_date": None,
            "followup_count": 0,
            "notes": "Filtered low priority."
        }
    ]

    saved_creators = []
    for c in sample_creators:
        inf = Influencer(campaign_id=campaign.id, **c)
        db.add(inf)
        saved_creators.append(inf)

    db.commit()

    # Add Outreach emails
    email1 = OutreachEmail(
        influencer_id=saved_creators[4].id,  # Maya
        recipient_email=saved_creators[4].email,
        subject=f"Partnership with {campaign.brand} x @{saved_creators[4].username}",
        body=f"Hi Maya,\n\nI came across your profile and really loved your breakdown on ceramides and hydration barriers.\n\nAt {campaign.brand}, we are launching our new Clean Barrier Serum and would love to collaborate: {campaign.offer_details}.\n\nAre you open to trying out our complete lab sample kit this week?\n\nBest regards,\n{campaign.sender_name}\n\nIf you'd rather not hear from us, just reply 'unsubscribe'.",
        email_type="initial",
        status="Pending Approval"
    )

    email2 = OutreachEmail(
        influencer_id=saved_creators[3].id,  # Chloe & Liam
        recipient_email=saved_creators[3].email,
        subject=f"Summer Collaboration: {campaign.brand} x Chloe & Liam",
        body=f"Hi Chloe & Liam,\n\nLoved your recent travel vlog—especially the travel routine tips!\n\nWe'd love to partner for our Summer Hydration kit: {campaign.offer_details}.\n\nLet us know if you're open to checking out the brief!\n\nBest,\n{campaign.sender_name}\n\nIf you'd rather not hear from us, just reply 'unsubscribe'.",
        email_type="initial",
        status="Sent",
        gmail_message_id="msg_sample_sent_101",
        gmail_thread_id="thread_chloe_004",
        sent_at=datetime.utcnow() - timedelta(days=1)
    )

    db.add_all([email1, email2])

    # Add Inbound Replies
    reply_interested = InboundReply(
        influencer_id=saved_creators[1].id,  # Marcus
        gmail_message_id="msg_reply_marcus_202",
        gmail_thread_id="thread_marcus_002",
        sender_email=saved_creators[1].email,
        snippet="Hey Alex, this sounds super interesting! Send over the details...",
        body="Hey Alex,\n\nThanks for reaching out! I checked out Aura Glow and love that the formula is fragrance-free. Could you send over the ingredient sheet and shipping details so I can test the kit?\n\nCheers,\nMarcus",
        category="interested",
        suggested_next_action="Send campaign brief, ingredient deck, and shipping intake form.",
        draft_reply=f"Hi Marcus,\n\nThrilled to hear you're excited! Attached is our clean ingredient certificate and here is the shipping link for your kit: https://auraglow.co/vip-intake\n\nLooking forward to having you on board!\n\nBest,\nAlex Rivera",
        draft_status="Pending Approval"
    )

    reply_pricing = InboundReply(
        influencer_id=saved_creators[0].id,  # Elena
        gmail_message_id="msg_reply_elena_303",
        gmail_thread_id="thread_elena_001",
        sender_email=saved_creators[0].email,
        snippet="Hi Alex! My standard rate for a dedicated Reel + 3 IG Stories is...",
        body="Hi Alex!\n\nThanks so much for thinking of me! My standard rate for a dedicated Reel + 3 IG Stories is $400 + product gifting. If that fits within your budget, I'd love to lock this in for next week's filming batch.\n\nWarmly,\nElena",
        category="pricing_enquiry",
        suggested_next_action="Confirm agreed $350-$400 sponsorship budget and send docusign agreement.",
        draft_reply="Hi Elena,\n\n$400 fits our campaign tier perfectly for the dedicated Reel! I've sent the simple agreement over to your inbox and our logistics team will courier the complete glow suite today.\n\nBest,\nAlex",
        draft_status="Approved"
    )

    db.add_all([reply_interested, reply_pricing])

    # Seed daily send counter
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    counter = DailySendCounter(send_date=today_str, count=7)
    db.add(counter)

    db.commit()
    db.close()
    print("Seed complete! Added 6 creators, campaign, emails, replies, and daily counter.")

if __name__ == "__main__":
    seed()
