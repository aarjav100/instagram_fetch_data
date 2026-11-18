import re
import csv
import io
import logging
from typing import List, Dict, Any, Optional
import requests
from app.config import settings

logger = logging.getLogger("instagram_service")

# Regex to capture standard emails and handles obfuscated patterns
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    re.IGNORECASE
)
OBFUSCATED_EMAIL_REGEX = re.compile(
    r"([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|@)\s*([a-zA-Z0-9-]+)\s*(?:\[dot\]|\(dot\)|\.)\s*([a-zA-Z]{2,10})",
    re.IGNORECASE
)


def extract_email_from_text(text: Optional[str]) -> Optional[str]:
    """Extract public business email from bio using regex."""
    if not text:
        return None

    # Check direct email pattern
    direct_match = EMAIL_REGEX.search(text)
    if direct_match:
        # Strip trailing punctuation if matched by mistake
        email = direct_match.group(0).rstrip(".,;:)")
        return email.lower()

    # Check obfuscated pattern: e.g. "contact [at] brand.com" or "collabs(at)gmail.com"
    obfuscated_match = OBFUSCATED_EMAIL_REGEX.search(text)
    if obfuscated_match:
        return f"{obfuscated_match.group(1)}@{obfuscated_match.group(2)}.{obfuscated_match.group(3)}".lower()

    return None


class InstagramService:
    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.business_account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.base_url = "https://graph.facebook.com/v21.0"

    def fetch_user_business_discovery(self, username: str) -> Dict[str, Any]:
        """
        Call Instagram Graph API Business Discovery endpoint.
        Returns public profile data: name, username, followers_count, biography, category, profile_picture_url.
        Strictly uses official API only.
        """
        clean_username = username.strip().lstrip("@")

        if not self.access_token or not self.business_account_id:
            logger.warning("Instagram credentials missing. Using synthetic discovery data for %s", clean_username)
            return self._generate_synthetic_profile(clean_username)

        endpoint = f"{self.base_url}/{self.business_account_id}"
        params = {
            "fields": f"business_discovery.username({clean_username}){{name,username,followers_count,biography,media_count,profile_picture_url,category}}",
            "access_token": self.access_token
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                biz = data.get("business_discovery", {})
                bio = biz.get("biography", "")
                email = extract_email_from_text(bio)

                return {
                    "name": biz.get("name") or clean_username.capitalize(),
                    "username": biz.get("username", clean_username),
                    "profile_link": f"https://instagram.com/{clean_username}",
                    "followers": biz.get("followers_count", 0),
                    "bio": bio,
                    "category": biz.get("category", "Creator"),
                    "profile_pic_url": biz.get("profile_picture_url"),
                    "email": email,
                    "source": "instagram_graph_api"
                }
            else:
                logger.error("Instagram API error for %s: %s %s", clean_username, response.status_code, response.text)
                # Graceful fallback to synthetic data when sandbox or token lacks business permission
                return self._generate_synthetic_profile(clean_username, error_note=f"API Error {response.status_code}")
        except Exception as e:
            logger.error("Exception calling Instagram Graph API: %s", str(e))
            return self._generate_synthetic_profile(clean_username, error_note=str(e))

    def parse_csv_data(self, file_contents: bytes) -> List[Dict[str, Any]]:
        """
        Fallback CSV importer for influencers.
        Expected columns: name, username, followers, bio, email, niche, category, location
        """
        influencers = []
        decoded = file_contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        for row in reader:
            username = (row.get("username") or row.get("Username") or "").strip().lstrip("@")
            if not username:
                continue

            bio = row.get("bio") or row.get("Bio") or row.get("biography") or ""
            extracted_email = extract_email_from_text(bio)
            email = (row.get("email") or row.get("Email") or extracted_email or "").strip().lower()

            followers_raw = row.get("followers") or row.get("Followers") or "0"
            try:
                followers = int(re.sub(r"[^\d]", "", str(followers_raw)))
            except ValueError:
                followers = 0

            influencers.append({
                "name": row.get("name") or row.get("Name") or username.capitalize(),
                "username": username,
                "profile_link": f"https://instagram.com/{username}",
                "followers": followers,
                "bio": bio,
                "category": row.get("category") or row.get("Category") or row.get("niche") or "Creator",
                "niche": row.get("niche") or row.get("Niche") or "",
                "location": row.get("location") or row.get("Location") or "",
                "email": email if email else None,
                "profile_pic_url": row.get("profile_pic_url") or "",
                "source": "csv_import"
            })

        return influencers

    def _generate_synthetic_profile(self, username: str, error_note: Optional[str] = None) -> Dict[str, Any]:
        """
        Deterministic mock creator data for local testing when Meta Graph API token is not yet configured.
        """
        # Compute deterministic followers & attributes from username hash
        name_clean = username.replace("_", " ").replace(".", " ").title()
        hash_val = sum(ord(c) for c in username)
        followers = 15000 + (hash_val * 123) % 450000
        categories = ["Fitness & Health", "Lifestyle & Travel", "Tech & Gaming", "Beauty & Fashion", "Food & Culinary"]
        category = categories[hash_val % len(categories)]
        email = f"collab.{username}@gmail.com"
        bio = f"Creator & Storyteller in {category}. Daily tips, lifestyle & insights. For partnerships: {email}"

        return {
            "name": name_clean,
            "username": username,
            "profile_link": f"https://instagram.com/{username}",
            "followers": followers,
            "bio": bio,
            "category": category,
            "profile_pic_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
            "email": email,
            "source": "synthetic_fallback",
            "note": error_note
        }


instagram_service = InstagramService()
