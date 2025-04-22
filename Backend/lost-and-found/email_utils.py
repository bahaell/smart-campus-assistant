import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_match_email(to_email: str, item_description: str, match_description: str, similarity: float):
    subject = "🔍 Possible Match Found for Your Lost Item"
    body = f"""Hello,

We have found an item that closely matches the description of your lost item.

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
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
