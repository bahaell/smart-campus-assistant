import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import re

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def send_match_email(to_email: str, item_description: str, match_description: str, similarity: float):
    """Send an email notification about a possible item match."""
    if not validate_email(to_email):
        print(f"Invalid email address: {to_email}")
        raise ValueError(f"Invalid email address: {to_email}")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env")
        raise ValueError("EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env")

    subject = "🔍 Possible Match Found for Your Lost Item"
    body = f"""Hello,

We have found an item that closely matches your lost item based on image analysis.

🔹 Your lost item: {item_description}
🔸 Matching found item: {match_description}
📊 Similarity score: {similarity:.2f}

Please visit the platform to verify and contact the person who found the item.

Best regards,
Lost and Found Team
"""
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        print(f"Connecting to smtp.gmail.com:465...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            print(f"Logging in with {EMAIL_ADDRESS}...")
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Login successful, sending email...")
            smtp.send_message(msg)
            print(f"Email successfully sent to {to_email}")
            return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}. Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env.")
        raise
    except smtplib.SMTPException as e:
        print(f"SMTP error while sending email to {to_email}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while sending email to {to_email}: {e}")
        raise