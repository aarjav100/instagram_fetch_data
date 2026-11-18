import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    client = TestClient(app)
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] /health response:", res.json(), flush=True)

    # 2. Dashboard stats
    res = client.get("/dashboard/stats")
    assert res.status_code == 200, f"Dashboard stats failed: {res.text}"
    data = res.json()
    print("[PASS] /dashboard/stats:", {
        "total_leads": data["total_leads"],
        "emails_sent": data["emails_sent"],
        "daily_sent_count": data["daily_sent_count"]
    }, flush=True)

    # 3. Influencer listing
    res = client.get("/influencers")
    assert res.status_code == 200
    creators = res.json()
    print(f"[PASS] /influencers returned {len(creators)} creators.", flush=True)

    # 4. Email queue
    res = client.get("/emails/queue")
    assert res.status_code == 200
    emails = res.json()
    print(f"[PASS] /emails/queue returned {len(emails)} emails.", flush=True)

    # 5. Follow-ups due
    res = client.get("/followups/due")
    assert res.status_code == 200
    due = res.json()
    print(f"[PASS] /followups/due returned {len(due)} due follow-ups.", flush=True)

    # 6. Replies
    res = client.get("/replies")
    assert res.status_code == 200
    replies = res.json()
    print(f"[PASS] /replies returned {len(replies)} inbox replies.", flush=True)

    # 7. Test research endpoint with mock/fallback
    res = client.post("/research", json={
        "brand": "Aura Test",
        "campaign": "Hydration Test",
        "niche": "Beauty",
        "usernames": ["skincare_glow_test"]
    })
    assert res.status_code == 200
    new_creators = res.json()
    print(f"[PASS] POST /research created {len(new_creators)} new creator:", new_creators[0]["username"], flush=True)

    # 8. Test email generation
    target_id = new_creators[0]["id"]
    res = client.post("/emails/generate", json={
        "influencer_ids": [target_id],
        "brand": "Aura Test",
        "sender_name": "Jordan",
        "offer": "Free skincare box + $200"
    })
    assert res.status_code == 200
    generated = res.json()
    print(f"[PASS] POST /emails/generate generated email id {generated[0]['id']}, status: {generated[0]['status']}", flush=True)

    # 9. Test approve email
    email_id = generated[0]["id"]
    res = client.post(f"/emails/approve/{email_id}", json={
        "subject": "Exclusive Collab with Aura Test"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "Approved"
    print(f"[PASS] POST /emails/approve/{email_id} updated status to Approved.", flush=True)

    # 10. Test send approved email
    res = client.post("/emails/send", json={"email_ids": [email_id]})
    assert res.status_code == 200
    print("[PASS] POST /emails/send sent email successfully:", res.json(), flush=True)

    # 11. Test simulate inbound reply
    res = client.post("/replies/simulate", json={
        "influencer_id": target_id,
        "reply_text": "Hey Jordan! I'd love to collaborate on this. What's the timeline?",
        "sender_email": "creator@test.com"
    })
    assert res.status_code == 200
    rep_data = res.json()
    print(f"[PASS] POST /replies/simulate: category={rep_data['category']}, action={rep_data['suggested_next_action']}", flush=True)

    print("\nALL 11 BACKEND API VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉", flush=True)
    import os
    os._exit(0)


if __name__ == "__main__":
    run_tests()

