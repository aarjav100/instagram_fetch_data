import json
import logging
import re
from typing import Dict, Any, Optional
import anthropic
from app.config import settings
from app.prompts import (
    INFLUENCER_FILTER_SYSTEM_PROMPT,
    INFLUENCER_FILTER_USER_PROMPT,
    EMAIL_GENERATION_SYSTEM_PROMPT,
    EMAIL_GENERATION_USER_PROMPT,
    REPLY_CLASSIFICATION_SYSTEM_PROMPT,
    REPLY_CLASSIFICATION_USER_PROMPT,
    FOLLOWUP_1_USER_PROMPT,
    FOLLOWUP_2_USER_PROMPT
)

logger = logging.getLogger("claude_service")


def clean_json_text(text: str) -> str:
    """Strip markdown code backticks and extract pure JSON."""
    cleaned = text.strip()
    # Strip markdown ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    # Find outermost JSON object
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        return match.group(0).strip()
    return cleaned.strip()


class ClaudeService:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> Optional[anthropic.Anthropic]:
        if not self._client and self.api_key:
            try:
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error("Failed to initialize Anthropic client: %s", e)
        return self._client

    def filter_influencer(
        self,
        brand: str,
        campaign: str,
        influencer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate influencer against campaign using Claude.
        Returns STRICT JSON: {niche, relevance_score (0-100), suitability_reason, profile_summary, priority}
        """
        inf_summary = {
            "name": influencer_data.get("name", ""),
            "username": influencer_data.get("username", ""),
            "bio": influencer_data.get("bio", ""),
            "followers": influencer_data.get("followers", 0),
            "category": influencer_data.get("category", ""),
            "location": influencer_data.get("location", "Not specified")
        }
        user_prompt = INFLUENCER_FILTER_USER_PROMPT.format(
            brand=brand,
            campaign=campaign,
            influencer_data=json.dumps(inf_summary)
        )

        if not self.client:
            logger.warning("Anthropic API key not configured. Using deterministic AI evaluation.")
            return self._fallback_filter(influencer_data, brand, campaign)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.2,
                system=INFLUENCER_FILTER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            raw_text = message.content[0].text
            cleaned = clean_json_text(raw_text)
            parsed = json.loads(cleaned)

            score = int(parsed.get("relevance_score", 70))
            score = max(0, min(100, score))
            priority = parsed.get("priority", "Medium")
            if priority not in ["High", "Medium", "Low"]:
                priority = "High" if score >= 80 else ("Medium" if score >= 50 else "Low")

            return {
                "niche": parsed.get("niche", influencer_data.get("category", "General")),
                "relevance_score": score,
                "profile_summary": parsed.get("profile_summary", "Creator engaged in targeted niche content."),
                "suitability_reason": parsed.get("suitability_reason", "Aligned with brand audience aesthetics."),
                "priority": priority
            }
        except Exception as e:
            logger.error("Error calling Claude for influencer filtering: %s", e)
            return self._fallback_filter(influencer_data, brand, campaign)

    def generate_cold_email(
        self,
        sender_name: str,
        brand: str,
        influencer_name: str,
        summary: str,
        offer: str
    ) -> Dict[str, str]:
        """
        Generate personalized cold outreach email.
        Returns STRICT JSON: {subject, body}
        """
        user_prompt = EMAIL_GENERATION_USER_PROMPT.format(
            sender_name=sender_name,
            brand=brand,
            influencer_name=influencer_name,
            summary=summary,
            offer=offer
        )

        if not self.client:
            logger.warning("Anthropic API key missing. Generating structured email draft.")
            return self._fallback_cold_email(sender_name, brand, influencer_name, summary, offer)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.4,
                system=EMAIL_GENERATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            raw_text = message.content[0].text
            cleaned = clean_json_text(raw_text)
            parsed = json.loads(cleaned)
            return {
                "subject": parsed.get("subject", f"Partnership with {brand} x {influencer_name}"),
                "body": parsed.get("body", "")
            }
        except Exception as e:
            logger.error("Error generating cold email with Claude: %s", e)
            return self._fallback_cold_email(sender_name, brand, influencer_name, summary, offer)

    def generate_followup(
        self,
        step: int,
        sender_name: str,
        brand: str,
        influencer_name: str,
        offer: str,
        original_subject: str
    ) -> Dict[str, str]:
        """Generate follow-up 1 or 2 email."""
        subject_prefix = original_subject if original_subject.startswith("Re:") else f"Re: {original_subject}"
        prompt_tmpl = FOLLOWUP_1_USER_PROMPT if step == 1 else FOLLOWUP_2_USER_PROMPT
        user_prompt = prompt_tmpl.format(
            sender_name=sender_name,
            brand=brand,
            influencer_name=influencer_name,
            offer=offer,
            original_subject=subject_prefix
        )

        if not self.client:
            return self._fallback_followup(step, sender_name, brand, influencer_name, offer, subject_prefix)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                temperature=0.3,
                system=EMAIL_GENERATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            raw_text = message.content[0].text
            cleaned = clean_json_text(raw_text)
            parsed = json.loads(cleaned)
            return {
                "subject": parsed.get("subject", subject_prefix),
                "body": parsed.get("body", "")
            }
        except Exception as e:
            logger.error("Error generating follow-up %s with Claude: %s", step, e)
            return self._fallback_followup(step, sender_name, brand, influencer_name, offer, subject_prefix)

    def classify_reply(self, reply_text: str) -> Dict[str, str]:
        """
        Classify inbound influencer reply into:
        interested | not_interested | pricing_enquiry | collaboration_request | opt_out | other
        Returns STRICT JSON: {category, suggested_next_action, draft_reply}
        """
        user_prompt = REPLY_CLASSIFICATION_USER_PROMPT.format(reply=reply_text)

        if not self.client:
            return self._fallback_classify_reply(reply_text)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.2,
                system=REPLY_CLASSIFICATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            raw_text = message.content[0].text
            cleaned = clean_json_text(raw_text)
            parsed = json.loads(cleaned)

            category = parsed.get("category", "other").lower().strip()
            valid_categories = [
                "interested", "not_interested", "pricing_enquiry",
                "collaboration_request", "opt_out", "other"
            ]
            if category not in valid_categories:
                category = "other"

            return {
                "category": category,
                "suggested_next_action": parsed.get("suggested_next_action", "Review message and respond"),
                "draft_reply": parsed.get("draft_reply", "")
            }
        except Exception as e:
            logger.error("Error classifying reply with Claude: %s", e)
            return self._fallback_classify_reply(reply_text)

    # Fallbacks when API key is pending or test environment
    def _fallback_filter(self, data: Dict[str, Any], brand: str, campaign: str) -> Dict[str, Any]:
        followers = data.get("followers", 0)
        category = data.get("category", "Lifestyle")
        bio = data.get("bio", "")

        score = 75
        if followers > 20000:
            score += 10
        if data.get("email"):
            score += 10
        if len(bio) > 40:
            score += 5
        score = min(98, score)

        priority = "High" if score >= 85 else ("Medium" if score >= 65 else "Low")
        summary = f"{data.get('name', 'Creator')} produces content in {category} with an active audience of {followers:,} followers."
        reason = f"Audience size and niche fit campaign '{campaign}' for {brand}."

        return {
            "niche": category,
            "relevance_score": score,
            "profile_summary": summary,
            "suitability_reason": reason,
            "priority": priority
        }

    def _fallback_cold_email(self, sender: str, brand: str, creator: str, summary: str, offer: str) -> Dict[str, str]:
        first_name = creator.split()[0] if creator else "there"
        subject = f"Collaboration idea with {brand} x @{first_name}"
        body = (
            f"Hi {first_name},\n\n"
            f"I came across your profile and really loved your work—especially how {summary.lower().rstrip('.')}.\n\n"
            f"At {brand}, we are launching a new creator campaign and would love to collaborate: {offer}.\n\n"
            f"Are you open to a quick chat this week or receiving a sample kit to test out?\n\n"
            f"Best regards,\n"
            f"{sender}\n"
            f"{brand} Partnerships Team\n\n"
            f"If you'd rather not hear from us, just reply 'unsubscribe'."
        )
        return {"subject": subject, "body": body}

    def _fallback_followup(self, step: int, sender: str, brand: str, creator: str, offer: str, subject: str) -> Dict[str, str]:
        first_name = creator.split()[0] if creator else "there"
        if step == 1:
            body = (
                f"Hi {first_name},\n\n"
                f"Following up briefly on my previous note regarding partnering with {brand} ({offer}).\n"
                f"We'd love to have you on board! Let me know if you'd like more details.\n\n"
                f"Best,\n{sender}\n\n"
                f"If you'd rather not hear from us, just reply 'unsubscribe'."
            )
        else:
            body = (
                f"Hi {first_name},\n\n"
                f"I know you're super busy, so this will be my last note! We'd still love to work with you in the future if timing aligns.\n\n"
                f"Wishing you all the best,\n{sender}\n\n"
                f"If you'd rather not hear from us, just reply 'unsubscribe'."
            )
        return {"subject": subject, "body": body}

    def _fallback_classify_reply(self, reply_text: str) -> Dict[str, str]:
        text_lower = reply_text.lower()
        if "unsubscribe" in text_lower or "remove" in text_lower or "stop emailing" in text_lower:
            return {
                "category": "opt_out",
                "suggested_next_action": "Mark lead as Opted Out and cease outreach.",
                "draft_reply": "Understood. You have been removed from our outreach list. Wishing you the best!"
            }
        elif "rate" in text_lower or "price" in text_lower or "fee" in text_lower or "$" in text_lower:
            return {
                "category": "pricing_enquiry",
                "suggested_next_action": "Send rate card request or budget tier details.",
                "draft_reply": "Thanks for getting back to us! Could you share your current media kit and standard rates for a post + reel?"
            }
        elif "interested" in text_lower or "send details" in text_lower or "sounds good" in text_lower or "love to" in text_lower:
            return {
                "category": "interested",
                "suggested_next_action": "Send brief, shipping form for product kit, and contract.",
                "draft_reply": "Awesome to hear you're excited! Here is the campaign brief and shipping link so we can send your kit: [link]."
            }
        elif "not interested" in text_lower or "no thanks" in text_lower or "pass" in text_lower:
            return {
                "category": "not_interested",
                "suggested_next_action": "Acknowledge politely and close thread.",
                "draft_reply": "Thanks for letting us know! Feel free to reach out anytime if your schedule opens up."
            }
        else:
            return {
                "category": "other",
                "suggested_next_action": "Read thread and craft custom response.",
                "draft_reply": "Thanks for your reply! Let me review this with the team and get back to you shortly."
            }


claude_service = ClaudeService()
