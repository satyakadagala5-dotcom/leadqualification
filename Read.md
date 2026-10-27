# WhatsApp Lead Qualification and Follow-up Agent

An automated lead management system built with Python, Streamlit, LangGraph, SQLite, FastAPI, and the WhatsApp Cloud API. The system captures leads, evaluates sales qualification conditions, sends eligible follow-up messages, and prepares qualified leads for appointment scheduling.

## Project Overview

The system manages leads through two primary stages:

- **MQL (Marketing Qualified Lead):** A lead that has not yet met all three SQL qualification conditions.
- **SQL (Sales Qualified Lead):** A lead that satisfies all three required conditions.

### SQL Qualification Conditions

A lead becomes an SQL only when all three conditions are true:

1. Requirement interest is confirmed.
2. A WhatsApp response has been received.
3. A call has been answered.

If any condition is false, the lead remains an MQL.

## Features

- Lead capture through a Streamlit dashboard.
- SQLite database for persistent lead records.
- LangGraph-based lead qualification workflow.
- WhatsApp Cloud API integration for outgoing messages.
- FastAPI webhook for receiving incoming WhatsApp messages.
- Follow-up scheduling at 24-hour intervals.
- Opt-in and opt-out tracking.
- Duplicate WhatsApp message detection.
- SQL lead export to Excel.
- Follow-up limits and qualification rechecks.

## Technology Stack

| Technology         | Purpose                                 |
| ------------------ | --------------------------------------- |
| Python             | Core application logic                  |
| Streamlit          | Lead management dashboard               |
| LangGraph          | Lead qualification workflow             |
| SQLite             | Lead and message storage                |
| FastAPI            | WhatsApp webhook endpoint               |
| WhatsApp Cloud API | Sending and receiving WhatsApp messages |
| APScheduler        | Periodic follow-up checks               |
| Pandas             | Lead data processing                    |
| OpenPyXL           | Excel file generation                   |
| python-dotenv      | Environment configuration               |

## Project Structure

```text
lead_qualification_project/
│
├── app.py
├── workflow.py
├── database.py
├── whatsapp_service.py
├── webhook.py
├── scheduler.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
└── leads.db                 # Created automatically
```

### File Responsibilities

- `app.py` — Streamlit dashboard for adding leads, updating qualification conditions, viewing lead records, and exporting SQL leads to Excel.
- `workflow.py` — LangGraph workflow that evaluates the SQL conditions and routes leads according to their status.
- `database.py` — SQLite database operations for lead records, message deduplication, consent, qualification, and follow-up scheduling.
- `whatsapp_service.py` — Sends WhatsApp text messages and approved template messages using Meta's API.
- `webhook.py` — Verifies Meta webhook requests, receives incoming messages, updates lead records, and triggers qualification.
- `scheduler.py` — Checks due follow-ups and sends messages to eligible MQLs.
- `requirements.txt` — Lists Python package dependencies.
- `.env` — Stores API credentials and configuration.
- `.gitignore` — Prevents credentials, database files, and temporary files from being committed.

## Prerequisites

Before running the project, install:

- Python 3.10 or a compatible newer Python version.
- pip and a virtual environment.
- A Meta developer account and configured WhatsApp Business Platform.
- A WhatsApp Cloud API access token and phone number ID.
- An approved WhatsApp message template for eligible follow-ups.
- A public HTTPS URL for webhook testing and deployment.

## Installation

### Step 1: Open the project folder

```bash
cd lead_qualification_project
```

### Step 2: Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file in the project root:

```dotenv
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_API_VERSION=v25.0

WHATSAPP_VERIFY_TOKEN=your_custom_verification_token
META_APP_SECRET=your_meta_app_secret

DATABASE_NAME=leads.db
FOLLOWUP_INTERVAL_HOURS=24
FOLLOWUP_TEMPLATE_NAME=lead_followup
WHATSAPP_TEMPLATE_LANGUAGE=en
MAX_FOLLOWUPS=3
```

Replace the placeholder values with your actual configuration.

Never upload `.env` to a public repository or share access tokens.

### Step 5: Initialize the database

```bash
python database.py
```

Expected output:

```text
Database initialized successfully.
```

The application creates `leads.db` automatically when the database initialization function runs.

## Running the Application

Run each component in a separate terminal with the virtual environment activated.

### Terminal 1: Streamlit Dashboard

```bash
streamlit run app.py
```

Streamlit normally opens at:

`http://localhost:8501`

Use the dashboard to add leads, update qualification conditions, view statuses, and download SQL records.

### Terminal 2: FastAPI Webhook

```bash
uvicorn webhook:app --host 0.0.0.0 --port 8000
```

The webhook endpoint is:

`/webhook`

Configure Meta to use the publicly reachable HTTPS URL for this endpoint and subscribe to incoming message events.

### Terminal 3: Follow-up Scheduler

```bash
python scheduler.py
```

The scheduler checks for due follow-ups periodically and attempts to send messages only to eligible leads.

## Workflow

1. A new lead is entered into the Streamlit dashboard.
2. The lead is stored in SQLite with its consent status.
3. LangGraph evaluates the three SQL qualification conditions.
4. If all conditions are true, the lead becomes an SQL and is ready for appointment processing.
5. If any condition is false, the lead remains an MQL.
6. The scheduler checks whether an MQL is eligible for a follow-up.
7. The WhatsApp Cloud API sends an eligible follow-up message.
8. The webhook receives incoming WhatsApp replies and updates the database.
9. The qualification workflow evaluates the updated conditions.
10. SQL leads can be exported to Excel for the appointment agent.

## Follow-up Rules

- Follow-ups are scheduled after 24 hours.
- Only eligible MQLs with the required opt-in are considered.
- Leads that opt out must not receive further follow-ups.
- Leads that become SQL must leave the follow-up process.
- A configured maximum follow-up count should be enforced.
- Eligibility should be checked immediately before sending.
- Outside the 24-hour customer-service window, an approved WhatsApp template is generally required.

## Excel Export

The dashboard generates an Excel workbook named:

`sql_leads.xlsx`

It contains records whose current status is SQL.

This file can be used as input to a separate appointment-booking agent or sales workflow.

## Testing Checklist

- [ ] Install all dependencies successfully.
- [ ] Initialize the SQLite database.
- [ ] Add a lead through the dashboard.
- [ ] Confirm that the lead is stored in SQLite.
- [ ] Verify that a lead with any failed SQL condition remains MQL.
- [ ] Verify that a lead with all three conditions true becomes SQL.
- [ ] Confirm that SQL leads can be exported to Excel.
- [ ] Test webhook verification and incoming replies.
- [ ] Confirm that duplicate incoming messages are ignored.
- [ ] Test opt-out handling.
- [ ] Test follow-up eligibility and timing.
- [ ] Confirm that the scheduler stops follow-ups for SQL and opted-out leads.

## Security and Production Considerations

- Keep API tokens and application secrets in environment variables.
- Verify webhook signatures using Meta's app secret.
- Use HTTPS for public webhook endpoints.
- Obtain and record appropriate messaging consent.
- Respect opt-out requests immediately.
- Store and process personal data according to applicable privacy requirements.
- Add retry handling and logging for API failures.
- Prevent concurrent scheduler workers from sending duplicate follow-ups.
- Record outbound WhatsApp message IDs and delivery statuses.
- Secure the dashboard before exposing it publicly.
- Back up the SQLite database or migrate to a managed database for higher-volume production workloads.

## Current Scope and Future Enhancements

The current project provides a foundation for lead capture, qualification, WhatsApp communication, follow-up scheduling, and Excel export.

Potential enhancements include:

- Automatic appointment booking and calendar integration.
- CRM integration.
- Delivery-status tracking.
- Lead scoring and analytics.
- Automated reporting and conversion metrics.
- A production-grade queue and retry mechanism.
- Role-based access control for sales teams.

## License

Add your preferred license before distributing or publishing this project.

```

```
