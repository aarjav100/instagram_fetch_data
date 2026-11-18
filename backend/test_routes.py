import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.main import health_check
from app.routers.dashboard import get_dashboard_metrics
from app.routers.influencers import get_influencers
from app.routers.research import run_research
from app.routers.emails import generate_cold_emails, approve_email, send_approved_emails, list_email_queue
from app.routers.followups import get_due_followups
from app.routers.replies import get_all_replies, simulate_reply, SimulateReplyRequest
from app.schemas import ResearchRequest, EmailGenerateRequest, EmailUpdateRequest

out = []
def log(msg):
    out.append(str(msg))
    print(msg)

db = SessionLocal()
try:
    # 1. Health check
    h = health_check()
    log(f"1. Health Check: {h['status']}, scheduler: {h['scheduler_active']}")

    # 2. Dashboard
    d = get_dashboard_metrics(db)
    log(f"2. Dashboard: leads={d.total_leads}, sent={d.emails_sent}, daily_sent={d.daily_sent_count}/{d.daily_limit}")

    # 3. Influencers list
    infs = get_influencers(db=db)
    log(f"3. Influencers count: {len(infs)}")

    # 4. Research
    req = ResearchRequest(
        brand="Glow Beauty Co",
        campaign="Summer Hydration",
        niche="Clean Beauty",
        usernames=["skincare_queen_maya"]
    )
    res_creators = run_research(req, db)
    log(f"4. Research: Created creator {res_creators[0].username} with score {res_creators[0].relevance_score}")

    # 5. Generate Email
    target_id = res_creators[0].id
    gen_req = EmailGenerateRequest(
        influencer_ids=[target_id],
        brand="Glow Beauty Co",
        sender_name="Sarah",
        offer="Free product box + 15% affiliate"
    )
    emails = generate_cold_emails(gen_req, db)
    log(f"5. Email Generated: ID {emails[0].id}, Subject: {emails[0].subject}")

    # 6. Approve Email
    app_res = approve_email(emails[0].id, EmailUpdateRequest(subject="Exclusive Partnership: Glow Beauty"), db)
    log(f"6. Email Approved: ID {app_res.id}, Status: {app_res.status}")

    # 7. Send Email
    send_res = send_approved_emails(db=db)
    log(f"7. Emails Sent: {send_res['sent_count']} sent")

    # 8. Follow-ups
    due = get_due_followups(db)
    log(f"8. Due Follow-ups: {len(due)} leads due")

    # 9. Simulate Inbound Reply
    sim = simulate_reply(SimulateReplyRequest(
        influencer_id=target_id,
        reply_text="Hi Sarah, this sounds wonderful! Send me the details and agreement."
    ), db)
    log(f"9. Reply Simulated: category={sim.category}, status={sim.influencer.status}")

    log("ALL 9 FUNCTIONAL ENDPOINT TESTS PASSED COMPLETELY! SUCCESS!")
finally:
    db.close()
    with open("endpoint_test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
