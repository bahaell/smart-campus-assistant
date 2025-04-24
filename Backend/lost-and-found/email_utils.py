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

def send_match_email(
    to_email: str,
    item_description: str,
    match_description: str,
    similarity: float,
    finder_email: str  
):
    """Send an email notification about a possible item match."""
    if not validate_email(to_email):
        raise ValueError(f"Invalid email address: {to_email}")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env")

    subject = "🔍 Possible Match Found for Your Lost Item"
    body = f"""Hello,

We have found an item that closely matches your lost item based on image analysis.

🔹 Your lost item: {item_description}
🔸 Matching found item: {match_description}
📊 Similarity score: {similarity:.2f}

📩 Contact the person who found the item: {finder_email}

Please visit the platform to verify and proceed.

Best regards,  
Lost and Found Team
"""
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"Email successfully sent to {to_email}")
            return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        raise
