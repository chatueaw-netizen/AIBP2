# SOP & Runbook — Daily Labor Market News Summary
**Version 1.0 | UALR AI-Powered Bus Final Project**

---

## 1. System Overview

| Component | Role |
|-----------|------|
| Make.com Scenario | Orchestrates the full workflow on a daily schedule |
| NewsAPI | Fetches today's top 5 labor market headlines |
| OpenAI GPT-4o | Summarizes news and generates 3 action items |
| Claude Code (text_cleaner.py) | Cleans and validates the GPT output |
| Gmail | Delivers the finished briefing by email |
| Google Drive | Archives every briefing as a timestamped .txt file |

**One operator can run this entire workflow. Daily manual effort: ~2 minutes to review the email.**

---

## 2. Architecture Diagram

```
[Make Scheduler 7 AM]
        |
        v
[NewsAPI GET /everything]   <-- fetches 5 articles about labor market
        |
        v
[OpenAI GPT-4o]             <-- summarizes + 3 action items (structured prompt)
        |
        v
[Claude Code /clean]        <-- deduplicates, fixes bullets, validates sections
        |
       / \
      v   v
[Gmail]  [Google Drive]     <-- sends email + archives .txt file
```

---

## 3. Credential Notes

> **NEVER put API keys inside the GPT prompt or the blueprint JSON you share publicly.**
> Store all secrets in Make.com's connection settings only.

| Secret | Where to Store | How to Get |
|--------|---------------|------------|
| NewsAPI Key | Make.com HTTP module → query param `apiKey` | newsapi.org → free account → API key |
| OpenAI API Key | Make.com → Connections → OpenAI connection | platform.openai.com → API keys |
| Gmail OAuth | Make.com → Connections → Gmail | OAuth popup in Make.com |
| Google Drive OAuth | Make.com → Connections → Google Drive | OAuth popup in Make.com |
| Google Drive Folder ID | Blueprint field `folderId` | Copy from Drive URL after `/folders/` |

---

## 4. Setup Instructions (Step-by-Step)

### A. Deploy the Python Text Cleaner

```bash
# 1. Install Python 3.11+ if not installed
# 2. Navigate to the text_cleaner folder
cd text_cleaner

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the service
python text_cleaner.py

# 5. Verify it's running
curl http://localhost:5000/health
# Expected: {"status": "ok", "timestamp": "..."}
```

To expose it to Make.com from your local machine, use ngrok:
```bash
# Install ngrok (ngrok.com), then:
ngrok http 5000
# Copy the https://xxxx.ngrok.io URL and paste into Module 4 of the blueprint
```

### B. Import the Make.com Blueprint

1. Log in to **make.com**
2. Click **Create a new scenario**
3. Click the **three-dot menu (...)** → **Import Blueprint**
4. Upload `make_blueprint.json`
5. Make.com will prompt you to connect each service — follow the OAuth flow for Gmail and Google Drive, and paste API keys for NewsAPI and OpenAI
6. In **Module 4**, replace `REPLACE_WITH_YOUR_SERVER_IP` with your ngrok URL (e.g., `https://xxxx.ngrok.io`)
7. In **Module 5**, replace `REPLACE_WITH_RECIPIENT_EMAIL` with your email address
8. In **Module 6**, replace `REPLACE_WITH_YOUR_GOOGLE_DRIVE_FOLDER_ID` with your Drive folder ID

### C. Set the Schedule

1. In Make.com, open the scenario
2. Click **Scheduling** → **Every day** → set time to **7:00 AM** your timezone
3. Save and **Activate** the scenario

---

## 5. Error-Handling Plan

| Failure Point | Symptom | Recovery Action |
|--------------|---------|-----------------|
| NewsAPI rate limit (100 req/day free) | Module 2 returns 429 | Upgrade plan or switch to Google News RSS URL (no key needed) |
| OpenAI API timeout | Module 3 returns error | Make retries up to 3×; check OpenAI status page |
| Text cleaner offline | Module 4 returns connection error | `ifempty()` in blueprint falls back to raw GPT text — email still sends |
| Gmail auth expired | Module 5 fails | Re-authorize Gmail connection in Make.com → Connections |
| Google Drive quota | Module 6 fails | Free up Drive space; Module 5 (email) still succeeds independently |

Make.com is configured with `maxErrors: 3` — the scenario retries up to 3 times before marking as failed and sending an error notification.

---

## 6. Verification Checklist (Run After Each Setup Change)

- [ ] `curl http://localhost:5000/health` returns `{"status": "ok"}`
- [ ] `curl -X POST http://localhost:5000/clean -H "Content-Type: application/json" -d '{"text":"- test\n- test\n• duplicate"}'` returns deduplicated output
- [ ] Make.com scenario shows green checkmarks on all 6 modules after a manual test run
- [ ] Email arrives in inbox with all sections: SUMMARY, KEY HIGHLIGHTS, ACTION ITEMS, MARKET SENTIMENT
- [ ] Google Drive folder contains a `.txt` file named `Labor-Market-YYYY-MM-DD.txt`
- [ ] `quality.all_sections_present` in the cleaner response is `true`

---

## 7. Metrics to Track (Evidence Pack)

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Time saved per day | 15–20 min vs. manual research | Compare clock time: manual vs. review-only |
| Accuracy (sections present) | 100% | `quality.all_sections_present` field in cleaner log |
| Cost per run | < $0.03 | OpenAI dashboard → usage per day |
| Delivery rate | 100% | Gmail sent folder count vs. scenario run count |
| Chars cleaned | Track weekly average | `stats.chars_removed` in cleaner response |

---

## 8. Privacy & Ethics Notes

- The system processes **publicly available news only** — no personal data.
- API keys are stored in Make.com's encrypted connection vault, not in the blueprint file.
- GPT output may contain errors; the daily email is for **review**, not automatic decision-making.
- NewsAPI free tier is rate-limited; do not increase `pageSize` beyond 5 without upgrading.

---

## 9. Quick-Start (Single Operator Daily Routine)

```
Morning (automated — no action needed):
  7:00 AM  → Make.com triggers
  7:01 AM  → News fetched, GPT writes briefing, cleaner formats it
  7:02 AM  → Email arrives in inbox + Drive file saved

Operator action:
  ~2 min   → Read email, act on the 3 action items
```

That's it. One person. One email. Three action items. Every day.
