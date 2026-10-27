
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v25.0")


def send_whatsapp_message(phone, message):
    """Send a text message during an eligible service window."""
    return _send_message(phone, {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    })


def send_followup_template(phone, name):
    """Send an approved template for an eligible follow-up."""
    template_name = os.getenv(
        "FOLLOWUP_TEMPLATE_NAME", "lead_followup"
    )
    language = os.getenv(
        "WHATSAPP_TEMPLATE_LANGUAGE", "en"
    )

    return _send_message(phone, {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": [{
                "type": "body",
                "parameters": [{
                    "type": "text",
                    "text": name or "there"
                }]
            }]
        }
    })


def _send_message(phone, payload):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        raise RuntimeError(
            "Configure WhatsApp credentials in .env"
        )

    url = (
        f"https://graph.facebook.com/{API_VERSION}/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    print("WhatsApp service configured.")