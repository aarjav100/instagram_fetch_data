import os
import base64
import time
import logging
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.config import settings
from app.database import SessionLocal
from app.models import DailySendCounter

logger = logging.getLogger("gmail_service")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]


class GmailService:
    def __init__(self):
        self.credentials_file = settings.GMAIL_CREDENTIALS_FILE
        self.token_file = settings.GMAIL_TOKEN_FILE
        self.daily_limit = settings.DAILY_SEND_LIMIT
        self.send_delay = settings.SEND_DELAY_SECONDS
        self._service = None

    def get_service(self):
        """Initialize and cache the Gmail API client."""
        if self._service:
            return self._service

        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, GMAIL_SCOPES)
            except Exception as e:
                logger.error("Error reading token file: %s", e)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error("Error refreshing Gmail credentials: %s", e)
            elif os.path.exists(self.credentials_file):
                logger.info("Credentials file exists. Manual OAuth authorization needed or token.json.")
            else:
                logger.warning("No Gmail credentials/token found at %s. API in sandbox mode.", self.token_file)
                return None

        if creds and creds.valid:
            self._service = build("gmail", "v1", credentials=creds)
            return self._service

        return None

    def check_and_increment_daily_limit(self) -> bool:
        """Enforce daily send limit (default 30). Returns True if allowed, False if exceeded."""
        today_str = date.today().isoformat()
        db = SessionLocal()
        try:
            counter = db.query(DailySendCounter).filter(DailySendCounter.send_date == today_str).first()
            if not counter:
                counter = DailySendCounter(send_date=today_str, count=0)
                db.add(counter)
                db.commit()
                db.refresh(counter)

            if counter.count >= self.daily_limit:
                logger.warning("Daily send limit reached: %s/%s", counter.count, self.daily_limit)
                return False

            counter.count += 1
            db.commit()
            return True
        finally:
            db.close()

    def get_daily_send_stats(self) -> Dict[str, int]:
        """Return current day's send count vs limit."""
        today_str = date.today().isoformat()
        db = SessionLocal()
        try:
            counter = db.query(DailySendCounter).filter(DailySendCounter.send_date == today_str).first()
            count = counter.count if counter else 0
            return {
                "sent_today": count,
                "daily_limit": self.daily_limit,
                "remaining": max(0, self.daily_limit - count)
            }
        finally:
            db.close()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        thread_id: Optional[str] = None,
        in_reply_to_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email through official Gmail API after approval.
        Enforces daily limit and rate limit delay.
        """
        # Check daily limit
        if not self.check_and_increment_daily_limit():
            raise Exception(f"Daily send limit of {self.daily_limit} reached. Try again tomorrow.")

        # Rate-limiting delay between sends
        time.sleep(self.send_delay)

        service = self.get_service()
        if not service:
            # Simulated send when token is not yet configured
            simulated_id = f"sim_{int(time.time() * 1000)}"
            assigned_thread_id = thread_id or f"thread_{simulated_id}"
            logger.info(
                "[SIMULATED GMAIL SEND] To: %s | Subject: %s | Thread: %s",
                to_email, subject, assigned_thread_id
            )
            return {
                "message_id": simulated_id,
                "thread_id": assigned_thread_id,
                "status": "sent",
                "mode": "simulated"
            }

        try:
            message = MIMEMultipart()
            message["to"] = to_email
            message["subject"] = subject
            if in_reply_to_message_id:
                message["In-Reply-To"] = in_reply_to_message_id
                message["References"] = in_reply_to_message_id

            msg_text = MIMEText(body_text, "plain")
            message.attach(msg_text)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {"raw": raw_message}
            if thread_id:
                body["threadId"] = thread_id

            sent = service.users().messages().send(
                userId=settings.GMAIL_USER_EMAIL,
                body=body
            ).execute()

            return {
                "message_id": sent.get("id"),
                "thread_id": sent.get("threadId"),
                "status": "sent",
                "mode": "live_gmail"
            }
        except Exception as e:
            logger.error("Gmail API error sending to %s: %s", to_email, e)
            raise e

    def fetch_thread_replies(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Fetch inbound messages in a Gmail thread.
        """
        service = self.get_service()
        if not service:
            return []

        try:
            thread_data = service.users().threads().get(
                userId=settings.GMAIL_USER_EMAIL,
                id=thread_id,
                format="full"
            ).execute()

            messages = thread_data.get("messages", [])
            inbound = []
            for msg in messages:
                payload = msg.get("payload", {})
                headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
                from_header = headers.get("from", "")

                # Skip messages sent by ourselves
                if settings.GMAIL_USER_EMAIL.lower() in from_header.lower():
                    continue

                snippet = msg.get("snippet", "")
                body = self._extract_body(payload) or snippet

                inbound.append({
                    "message_id": msg.get("id"),
                    "thread_id": thread_id,
                    "sender_email": from_header,
                    "snippet": snippet,
                    "body": body,
                    "internal_date": int(msg.get("internalDate", 0)) / 1000
                })
            return inbound
        except Exception as e:
            logger.error("Error fetching thread %s: %s", thread_id, e)
            return []

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Recursively extract plain text message body from MIME payload."""
        if "data" in payload.get("body", {}):
            try:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            except Exception:
                pass

        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                try:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
            elif part.get("parts"):
                res = self._extract_body(part)
                if res:
                    return res

        return ""


gmail_service = GmailService()
