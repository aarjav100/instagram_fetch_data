import os
import re
import sys
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import gspread

load_dotenv()

if not os.path.exists("token.json"):
    print("ERROR: token.json not found in the current folder. Run python generate_token.py first.")
    sys.exit(1)

creds = Credentials.from_authorized_user_file("token.json")

print("\n===============================")
print("  GOOGLE SERVICES CONNECTION TEST")
print("===============================\n")

# --- Test 1: Google Sheets ---
print("--- [Test 1] Google Sheets Connection ---")
raw_sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()

if not raw_sheet_id:
    print("Warning: GOOGLE_SHEET_ID is not set in .env")
else:
    try:
        gc = gspread.authorize(creds)
        # Extract pure ID if full URL was pasted in .env
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_sheet_id)
        sheet_key = match.group(1) if match else raw_sheet_id

        sh = gc.open_by_key(sheet_key)
        tab_name = os.getenv("GOOGLE_SHEET_TAB", "Leads")
        try:
            sheet = sh.worksheet(tab_name)
        except Exception:
            sheet = sh.sheet1

        headers = sheet.row_values(1)
        print(f"Connected to Spreadsheet: '{sh.title}' (Tab: '{sheet.title}')")
        print("Sheet headers:", headers if headers else "[Empty worksheet]")
    except Exception as e:
        print(f"Google Sheets test error: {e}")

print("\n--- [Test 2 & 3] Gmail Send & Thread Read ---")
# Check recipient email
test_recipient = os.getenv("TEST_EMAIL_TO", "aarjav100jain@gmail.com").strip()
if len(sys.argv) > 1:
    test_recipient = sys.argv[1]

print(f"Sending test email to: {test_recipient}")

try:
    gmail = build("gmail", "v1", credentials=creds)
    msg = MIMEText("This is a test email from my AI Instagram Influencer Outreach Automation.")
    msg["to"] = test_recipient
    msg["subject"] = "AI Outreach Automation - Test email"
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    sent = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    print("Email sent successfully!")
    print("Message ID:", sent["id"])
    print("Thread ID :", sent["threadId"])

    # --- Test 3: Gmail read thread ---
    thread = gmail.users().threads().get(userId="me", id=sent["threadId"]).execute()
    messages_count = len(thread.get("messages", []))
    print("\n--- [Test 3] Thread Read Verification ---")
    print("Messages in thread:", messages_count)
    print("\nSUCCESS: All tests completed! Check your inbox for the test email.")

except Exception as e:
    print(f"Gmail test error: {e}")
