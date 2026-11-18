import os
import logging
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials
from app.config import settings

logger = logging.getLogger("sheets_service")

SHEET_COLUMNS = [
    "Name",
    "Username",
    "Profile Link",
    "Niche",
    "Followers",
    "Email",
    "Location",
    "Summary",
    "Score",
    "Status",
    "Thread ID",
    "Last Email Date",
    "Follow-up Count",
    "Notes"
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class SheetsService:
    def __init__(self):
        self.service_account_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
        self.token_path = getattr(settings, "GMAIL_TOKEN_FILE", "token.json")
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.sheet_name = settings.GOOGLE_SHEET_NAME
        self._client: Optional[gspread.Client] = None
        self._worksheet = None

    def _get_client(self) -> Optional[gspread.Client]:
        if self._client:
            return self._client

        # 1. Try authorized user token.json first
        if os.path.exists(self.token_path):
            try:
                from google.oauth2.credentials import Credentials as UserCredentials
                creds = UserCredentials.from_authorized_user_file(self.token_path)
                self._client = gspread.authorize(creds)
                logger.info("Connected to Google Sheets via token.json.")
                return self._client
            except Exception as e:
                logger.warning("Could not authorize Google Sheets from token.json: %s", e)

        # 2. Fall back to Service Account JSON
        if os.path.exists(self.service_account_path):
            try:
                creds = Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=SCOPES
                )
                self._client = gspread.authorize(creds)
                return self._client
            except Exception as e:
                logger.error("Failed to authenticate service account: %s", e)

        logger.warning("No Google Sheets credentials found. Live syncing disabled.")
        return None

    def get_or_create_worksheet(self):
        client = self._get_client()
        if not client:
            return None

        try:
            target_key = self.sheet_id.strip() if self.sheet_id else ""
            if "/d/" in target_key:
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", target_key)
                if match:
                    target_key = match.group(1)

            if target_key:
                spreadsheet = client.open_by_key(target_key)
            else:
                try:
                    spreadsheet = client.open(self.sheet_name)
                except gspread.SpreadsheetNotFound:
                    spreadsheet = client.create(self.sheet_name)

            worksheet = spreadsheet.sheet1
            existing_headers = worksheet.row_values(1)
            if not existing_headers:
                worksheet.update("A1:N1", [SHEET_COLUMNS])

            self._worksheet = worksheet
            return worksheet
        except Exception as e:
            logger.error("Failed to access/initialize Google Sheet: %s", e)
            return None

    def sync_influencer(self, influencer_dict: Dict[str, Any]) -> bool:
        """
        Insert or update influencer in Google Sheet.
        De-duplicates by username and email.
        """
        ws = self.get_or_create_worksheet()
        if not ws:
            logger.info("Sheet offline: Influencer %s kept in local SQLite CRM.", influencer_dict.get("username"))
            return False

        try:
            records = ws.get_all_records()
            target_username = str(influencer_dict.get("username", "")).strip().lower()
            target_email = str(influencer_dict.get("email", "") or "").strip().lower()

            row_index = None
            for idx, r in enumerate(records, start=2):  # Header is row 1
                row_user = str(r.get("Username", "")).strip().lower()
                row_email = str(r.get("Email", "")).strip().lower()

                if (target_username and row_user == target_username) or (target_email and row_email == target_email):
                    row_index = idx
                    break

            row_values = [
                influencer_dict.get("name", ""),
                influencer_dict.get("username", ""),
                influencer_dict.get("profile_link", ""),
                influencer_dict.get("niche", ""),
                influencer_dict.get("followers", 0),
                influencer_dict.get("email", ""),
                influencer_dict.get("location", ""),
                influencer_dict.get("profile_summary", ""),
                influencer_dict.get("relevance_score", 0),
                influencer_dict.get("status", "New Lead"),
                influencer_dict.get("thread_id", ""),
                str(influencer_dict.get("last_email_date") or ""),
                influencer_dict.get("followup_count", 0),
                influencer_dict.get("notes", "")
            ]

            if row_index:
                # Update existing row
                cell_range = f"A{row_index}:N{row_index}"
                ws.update(cell_range, [row_values])
                logger.info("Updated Google Sheet row %s for %s", row_index, target_username)
            else:
                # Append new row
                ws.append_row(row_values)
                logger.info("Appended new Google Sheet row for %s", target_username)

            return True
        except Exception as e:
            logger.error("Error syncing influencer to Google Sheets: %s", e)
            return False

    def batch_sync(self, influencers: List[Dict[str, Any]]) -> int:
        """Sync a list of influencers, de-duplicating by username and email."""
        synced_count = 0
        for inf in influencers:
            if self.sync_influencer(inf):
                synced_count += 1
        return synced_count


sheets_service = SheetsService()
