# AuraReach - AI Instagram Influencer Outreach Automation

An end-to-end, enterprise-grade influencer marketing outreach automation system built with **FastAPI**, **SQLite (SQLAlchemy)**, **Anthropic Claude 3.5 Sonnet**, **Instagram Graph API (Business Discovery)**, **Google Sheets CRM (gspread)**, **Gmail API (google-api-python-client)**, **APScheduler**, and a modern **React + Vite + Tailwind CSS** dashboard.

---

## 🚀 Key Modules & Architecture

### 1. Influencer Research (`POST /research` & `POST /research/csv`)
- **Official Instagram Graph API Only**: Connects to the official Meta Instagram Graph API Business Discovery endpoint (`GET /{ig-business-account-id}?fields=business_discovery.username({username}){...}`) to fetch public profile data (name, username, followers, biography, media count, category, profile picture).
- **Public Business Email Extraction**: Parses creator bios via robust regex capturing both standard formats (`name@domain.com`) and obfuscated formats (`name [at] domain dot com`).
- **CSV Import Fallback**: Upload CSV creator lists with columns `username, name, followers, bio, email, niche, location` for instant ingestion.
- **Strict Compliance**: Zero web scraping; relies exclusively on official APIs or user-imported files.

### 2. AI Filtering with Claude (`prompts.py`)
- Evaluates creators against your brand campaign with Claude requesting **STRICT JSON**:
  ```json
  {
    "niche": "Clean Skincare & Wellness",
    "relevance_score": 94,
    "profile_summary": "max 2 sentences",
    "suitability_reason": "High relevance to summer hydration products",
    "priority": "High|Medium|Low"
  }
  ```
- Automatically filters and sorts candidate influencers by score.

### 3. Google Sheets CRM (`gspread`)
- Automatic de-duplication by `username` and `email` before updating or inserting.
- **14 Standardized CRM Columns**:
  1. `Name`
  2. `Username`
  3. `Profile Link`
  4. `Niche`
  5. `Followers`
  6. `Email`
  7. `Location`
  8. `Summary`
  9. `Score`
  10. `Status`
  11. `Thread ID`
  12. `Last Email Date`
  13. `Follow-up Count`
  14. `Notes`
- **9 Core Pipeline Statuses**:
  - `New Lead`
  - `Email Available`
  - `Email Sent`
  - `Follow-up Due`
  - `Replied`
  - `Interested`
  - `Not Interested`
  - `Collaboration Confirmed`
  - `Opted Out`

### 4. Cold Email Generation & Gmail API Sending
- **Claude Cold Email Copywriter**: Generates personalized emails under 120 words referencing specific elements from creator bios, presenting the collaboration offer, giving a clear CTA, sender signature, and mandatory opt-out line:
  > *"If you'd rather not hear from us, just reply 'unsubscribe'."*
- **Mandatory Human-in-the-Loop Approval**: Emails are saved as `"Pending Approval"`. Only approved emails can be dispatched via `POST /emails/send`.
- **Anti-Spam Throttling**: Enforces daily send limits (default **30 emails/day**) and safety delays between API requests. Tracks Gmail `threadId` and `messageId`.

### 5. Automated Follow-up Sequences (`APScheduler`)
- Background scheduler evaluates active leads every hour:
  - **Step 1**: Leads in `"Email Sent"` with no reply after **3 to 5 days** receive **Follow-up 1**.
  - **Step 2**: Leads with no reply after **5 to 7 more days** receive **Follow-up 2 (final polite break-up note)**. Max 2 follow-ups.
- Follow-ups maintain threading continuity in Gmail by referencing the original `threadId`, `In-Reply-To`, and `References`.
- **Automatic Cease**: Sequences automatically stop immediately if lead status becomes `Replied`, `Not Interested`, or `Opted Out`.

### 6. Reply Management & AI Classification
- Background job polls Gmail threads periodically for new inbound messages.
- Claude classifies replies into:
  - `interested`
  - `not_interested`
  - `pricing_enquiry`
  - `collaboration_request`
  - `opt_out`
  - `other`
- Claude suggests the `suggested_next_action` and drafts a contextual response.
- Automatically updates Google Sheet and SQLite lead status (`Interested`, `Opted Out`, `Replied`).
- Drafts require human review and approval before sending.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, error handling, health check
│   │   ├── config.py            # Pydantic Settings & environment variables
│   │   ├── database.py          # SQLAlchemy SQLite connection setup
│   │   ├── models.py            # Influencer, Campaign, OutreachEmail, InboundReply, DailySendCounter
│   │   ├── schemas.py           # Pydantic request/response validation schemas
│   │   ├── prompts.py           # Claude prompt templates verbatim
│   │   ├── scheduler.py         # APScheduler background tasks for follow-ups and reply polling
│   │   ├── services/
│   │   │   ├── instagram_service.py # Official Meta Business Discovery & bio email regex extraction
│   │   │   ├── claude_service.py    # Anthropic SDK wrapper, strict JSON parser & fallbacks
│   │   │   ├── sheets_service.py    # gspread CRM sync with username/email de-duplication
│   │   │   ├── gmail_service.py     # Gmail API client, daily limit meter, thread dispatch
│   │   │   ├── followup_service.py  # Sequence logic (Follow-up 1 & 2)
│   │   │   └── reply_service.py     # Inbound message classification & status transitions
│   │   └── routers/
│   │       ├── research.py      # POST /research, POST /research/csv
│   │       ├── influencers.py   # GET, PATCH, DELETE /influencers
│   │       ├── emails.py        # POST /emails/generate, approve, reject, send, queue, stats
│   │       ├── followups.py     # GET /followups/due, POST /followups/trigger-check
│   │       ├── replies.py       # GET /replies, POST /replies/poll, simulate, approve, send
│   │       └── dashboard.py     # GET /dashboard/stats
│   ├── seed_data.py             # Pre-populates 6 realistic creator pipeline leads & metrics
│   ├── test_routes.py           # Comprehensive automated verification suite
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx       # Top bar, daily send progress meter, online health ping
│   │   │   ├── Sidebar.jsx      # Navigation between all 6 pages with badge counters
│   │   │   ├── StatCard.jsx     # Modern metric cards with color accents
│   │   │   └── PipelineChart.jsx # Interactive distribution bar chart
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx            # KPI overview, pipeline chart, safety quota meter
│   │   │   ├── CampaignSetup.jsx        # Parameter form, username list, CSV upload fallback
│   │   │   ├── InfluencerTable.jsx      # CRM directory with search, filters, score badges, status dropdown
│   │   │   ├── EmailApprovalQueue.jsx   # Editable subject & body drafts, Approve, Reject, Send Approved
│   │   │   ├── FollowUps.jsx            # Leads due for Follow-up 1 & 2, timeline check
│   │   │   └── InboxReplies.jsx         # Inbound reply sentiment tags, suggested action, draft editor & simulator
│   │   ├── context/
│   │   │   └── ToastContext.jsx # Toast notifications
│   │   ├── api.js               # Axios client connected to VITE_API_BASE_URL
│   │   ├── App.jsx
│   │   ├── index.css            # Tailwind directives & dark mode scrollbars
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── .env
└── README.md
```

---

## 🛠️ Quickstart Setup Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

---

### Step 1: Backend Setup

1. Open a terminal and navigate to the project root:
   ```bash
   cd "f:/projects/projects/intagram fetcher info/backend"
   ```

2. Activate the Python virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - On Linux / macOS:
     ```bash
     source venv/bin/activate
     ```

3. Configure your `.env` file:
   Copy `.env.example` to `.env` and fill in your API credentials:
   ```env
   APP_ENV=development
   DATABASE_URL=sqlite:///./influencer_crm.db

   # Anthropic Claude API Key (https://console.anthropic.com/)
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

   # Instagram Graph API (Official Business Discovery)
   INSTAGRAM_ACCESS_TOKEN=EAA...
   INSTAGRAM_BUSINESS_ACCOUNT_ID=178414...

   # Google Sheets CRM Integration (gspread)
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_SHEET_NAME=Influencer Outreach CRM

   # Gmail API
   GMAIL_CREDENTIALS_FILE=gmail_credentials.json
   GMAIL_TOKEN_FILE=token.json
   GMAIL_USER_EMAIL=me

   # Daily safe send limits
   DAILY_SEND_LIMIT=30
   SEND_DELAY_SECONDS=3
   ```

4. Seed the database with realistic demonstration leads:
   ```bash
   python seed_data.py
   ```

5. Run the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Backend documentation will be live at:
   - Swagger UI: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

---

### Step 2: Frontend Setup

1. Open a new terminal in the `frontend` directory:
   ```bash
   cd "f:/projects/projects/intagram fetcher info/frontend"
   ```

2. Verify `.env` points to your FastAPI backend:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 🤖 Exact Claude Prompts Reference (`app/prompts.py`)

### 1. Influencer Filtering Prompt
```text
You are an influencer-marketing analyst. Brand: {brand}. Campaign: {campaign}.
Influencer data: {name, username, bio, followers, category, location}.
Return ONLY JSON: {"niche": "", "relevance_score": 0-100,
"profile_summary": "max 2 sentences", "suitability_reason": "", "priority": "High|Medium|Low"}
```

### 2. Cold Outreach Email Generation Prompt
```text
Write a short (under 120 words), friendly, personalized cold email from {sender_name}
at {brand} to {influencer_name}. Mention something specific from their profile:
{summary}. Explain the collaboration: {offer}. End with one clear CTA (a reply or a
call). Include a signature and this line: "If you'd rather not hear from us, just
reply 'unsubscribe'." Return JSON: {"subject": "", "body": ""}
```

### 3. Inbound Reply Classification Prompt
```text
Classify this influencer reply into: interested, not_interested, pricing_enquiry,
collaboration_request, opt_out, other. Return JSON: {"category": "",
"suggested_next_action": "", "draft_reply": ""}. Reply text: {reply}
```

---

## 📡 API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health, scheduler state, connected integrations |
| `GET` | `/dashboard/stats` | KPI metrics, pipeline stage distribution, send meter |
| `POST` | `/research` | Instagram Graph API Discovery + Claude evaluation |
| `POST` | `/research/csv` | CSV upload fallback with Claude scoring |
| `GET` | `/influencers` | Filterable, sortable, searchable CRM directory |
| `PATCH`| `/influencers/{id}`| Update status, notes, or email; syncs to Google Sheets |
| `DELETE`| `/influencers/{id}`| Delete creator lead |
| `POST` | `/emails/generate` | Generate personalized Claude drafts (Pending Approval) |
| `GET` | `/emails/queue` | List emails filtered by status |
| `GET` | `/emails/stats` | Current daily send count vs limit |
| `POST` | `/emails/approve/{id}` | Authorize email for Gmail dispatch |
| `POST` | `/emails/reject/{id}` | Reject generated draft |
| `POST` | `/emails/send` | Dispatches approved emails via Gmail with throttling |
| `GET` | `/followups/due` | Lists leads eligible for Follow-up 1 or Follow-up 2 |
| `POST` | `/followups/trigger-check`| Evaluates timelines and creates follow-up drafts |
| `POST` | `/followups/generate/{id}`| Creates draft follow-up for a single influencer |
| `GET` | `/replies` | Inbound replies classified by Claude |
| `POST` | `/replies/poll` | Polls Gmail threads for new incoming messages |
| `POST` | `/replies/simulate` | Simulates creator response for live testing |
| `POST` | `/replies/approve/{id}` | Edits or authorizes AI draft reply |
| `POST` | `/replies/send/{id}` | Dispatches draft reply in same Gmail thread |

---

## 🧪 Verification & Automated Testing

Run the included verification suite:
```bash
python backend/test_routes.py
```
This tests all 9 core subsystems:
1. Health check & configuration report
2. Dashboard metrics aggregation
3. Influencer filtering and query binding
4. Instagram Business Discovery & Claude scoring
5. Personalized email generation
6. Human approval authorization
7. Safe throttled Gmail dispatch
8. Follow-up sequence timeline evaluation
9. Inbound message classification, action recommendation, and CRM status updates
