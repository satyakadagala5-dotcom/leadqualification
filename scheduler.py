
import os
import logging

from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

from database import (
    initialize_database,
    get_due_followups,
    get_lead,
    reserve_followup,
    schedule_followup,
    mark_followup_sent,
)
from whatsapp_service import send_followup_template

load_dotenv()
initialize_database()

logging.basicConfig(level=logging.INFO)

MAX_FOLLOWUPS = int(os.getenv("MAX_FOLLOWUPS", "3"))
scheduler = BlockingScheduler(timezone="UTC")


def run_followups():
    for due_lead in get_due_followups():
        lead_id = due_lead["lead_id"]

        # Refresh the lead immediately before sending.
        lead = get_lead(lead_id)

        if not lead:
            continue

        if (
            lead["lead_status"] != "MQL"
            or not lead["opt_in"]
            or lead["opted_out"]
            or all(
                lead[field] == 1
                for field in (
                    "requirement_interest",
                    "whatsapp_sms_response",
                    "call_answered",
                )
            )
        ):
            continue

        if lead["followup_sent"] >= MAX_FOLLOWUPS:
            continue

        if not reserve_followup(lead_id):
            continue

        try:
            result = send_followup_template(
                lead["phone"],
                lead["name"] or "there",
            )

            # Count only after the API accepts the request.
            mark_followup_sent(lead_id)

            # Repeat the 24-hour loop if still eligible.
            updated = get_lead(lead_id)

            if (
                updated
                and updated["lead_status"] == "MQL"
                and updated["opt_in"]
                and not updated["opted_out"]
                and updated["followup_sent"] < MAX_FOLLOWUPS
            ):
                schedule_followup(lead_id, hours=24)

            logging.info(
                "Follow-up accepted for lead %s; response=%s",
                lead_id,
                result.get("messages", [{}])[0].get("id"),
            )

        except Exception:
            logging.exception("Follow-up failed for lead %s", lead_id)
            try:
                if get_lead(lead_id) and get_lead(lead_id)["lead_status"] == "MQL":
                    schedule_followup(lead_id, hours=1)
            except Exception:
                logging.exception("Failed to reschedule follow-up for lead %s", lead_id)


if __name__ == "__main__":
    scheduler.add_job(
        run_followups,
        trigger="interval",
        minutes=5,
        id="lead_followups",
        max_instances=1,
        coalesce=True,
    )

    logging.info("Follow-up scheduler started.")
    scheduler.start()