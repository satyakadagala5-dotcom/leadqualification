import sqlite3
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DATABASE_NAME", "leads.db")


# Connect to the database
def get_connection():
    connection = sqlite3.connect(DB_NAME, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


# Create database tables
def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT NOT NULL,
                requirement_interest INTEGER DEFAULT 0,
                whatsapp_sms_response INTEGER DEFAULT 0,
                call_answered INTEGER DEFAULT 0,
                lead_status TEXT DEFAULT 'MQL',
                opt_in INTEGER DEFAULT 0,
                opted_out INTEGER DEFAULT 0,
                last_inbound_at TEXT,
                followup_due_at TEXT,
                followup_sent INTEGER DEFAULT 0
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT PRIMARY KEY,
                processed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Add a new lead
def add_lead(
    lead_id,
    name,
    phone,
    requirement_interest=False,
    call_answered=False,
    opt_in=False,
):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO leads (
                lead_id, name, phone,
                requirement_interest, call_answered, opt_in
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(lead_id) DO NOTHING
        """, (
            str(lead_id),
            name,
            phone,
            int(requirement_interest),
            int(call_answered),
            int(opt_in),
        ))

        added = cursor.rowcount == 1

    if added:
        qualify_lead(lead_id)

    return added


# Get one lead
def get_lead(lead_id):
    with get_connection() as connection:
        lead = connection.execute("""
            SELECT *
            FROM leads
            WHERE lead_id = ?
        """, (str(lead_id),)).fetchone()

        return dict(lead) if lead else None


# Update lead qualification conditions
def update_sql_conditions(
    lead_id,
    requirement_interest=None,
    whatsapp_sms_response=None,
    call_answered=None,
):
    fields = {
        "requirement_interest": requirement_interest,
        "whatsapp_sms_response": whatsapp_sms_response,
        "call_answered": call_answered,
    }

    with get_connection() as connection:
        for column, value in fields.items():
            if value is not None:
                connection.execute(
                    f"""
                    UPDATE leads
                    SET {column} = ?
                    WHERE lead_id = ?
                    """,
                    (int(value), str(lead_id)),
                )

    return qualify_lead(lead_id)


# Determine whether a lead is MQL or SQL
def qualify_lead(lead_id):
    with get_connection() as connection:
        lead = connection.execute("""
            SELECT requirement_interest,
                   whatsapp_sms_response,
                   call_answered,
                   opted_out
            FROM leads
            WHERE lead_id = ?
        """, (str(lead_id),)).fetchone()

        if not lead:
            return None

        if lead["opted_out"]:
            return "OPTED_OUT"

        is_sql = all(
            lead[field] == 1
            for field in (
                "requirement_interest",
                "whatsapp_sms_response",
                "call_answered",
            )
        )

        status = "SQL" if is_sql else "MQL"

        connection.execute("""
            UPDATE leads
            SET lead_status = ?,
                followup_due_at = CASE
                    WHEN ? = 'SQL' THEN NULL
                    ELSE followup_due_at
                END
            WHERE lead_id = ?
        """, (status, status, str(lead_id)))

        return status


# Record an incoming WhatsApp reply once
def record_whatsapp_reply(lead_id, message_id):
    if not message_id:
        return False

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO processed_messages (message_id)
            VALUES (?)
            ON CONFLICT(message_id) DO NOTHING
        """, (str(message_id),))

        if cursor.rowcount == 0:
            return False

        connection.execute("""
            UPDATE leads
            SET whatsapp_sms_response = 1,
                last_inbound_at = ?,
                followup_due_at = NULL
            WHERE lead_id = ?
        """, (
            datetime.now(timezone.utc).isoformat(),
            str(lead_id),
        ))

    qualify_lead(lead_id)
    return True


# Stop future follow-ups when a lead opts out
def opt_out_lead(lead_id):
    with get_connection() as connection:
        connection.execute("""
            UPDATE leads
            SET opted_out = 1,
                opt_in = 0,
                followup_due_at = NULL
            WHERE lead_id = ?
        """, (str(lead_id),))

    return True


# Schedule a follow-up
def schedule_followup(lead_id, hours=24):
    due_time = (
        datetime.now(timezone.utc) + timedelta(hours=hours)
    ).isoformat()

    with get_connection() as connection:
        connection.execute("""
            UPDATE leads
            SET followup_due_at = ?
            WHERE lead_id = ?
              AND lead_status = 'MQL'
              AND opt_in = 1
              AND opted_out = 0
        """, (due_time, str(lead_id)))

    return due_time


# Get leads whose follow-ups are due
def get_due_followups():
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        leads = connection.execute("""
            SELECT *
            FROM leads
            WHERE lead_status = 'MQL'
              AND opt_in = 1
              AND opted_out = 0
              AND followup_due_at IS NOT NULL
              AND followup_due_at <= ?
              AND followup_sent < ?
            ORDER BY followup_due_at ASC
        """, (
            now,
            int(os.getenv("MAX_FOLLOWUPS", "3")),
        )).fetchall()

        return [dict(lead) for lead in leads]


def reserve_followup(lead_id):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE leads
            SET followup_due_at = NULL
            WHERE lead_id = ?
              AND lead_status = 'MQL'
              AND opt_in = 1
              AND opted_out = 0
              AND followup_due_at IS NOT NULL
              AND followup_due_at <= ?
              AND followup_sent < ?
        """, (
            str(lead_id),
            now,
            int(os.getenv("MAX_FOLLOWUPS", "3")),
        ))

    return cursor.rowcount > 0


# Record that a follow-up was sent
def mark_followup_sent(lead_id):
    with get_connection() as connection:
        connection.execute("""
            UPDATE leads
            SET followup_sent = followup_sent + 1
            WHERE lead_id = ?
        """, (str(lead_id),))

    return True


# Run this file directly to initialize the database
if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")