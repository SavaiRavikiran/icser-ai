"""Email parsing: extract body, attachments, sender metadata."""
import email
import email.policy
import json
import structlog
from io import BytesIO


logger = structlog.get_logger()


async def parse_email(email_data: str) -> str:
    """Parse raw email data (base64 or MIME) and extract text content."""
    try:
        import base64
        raw = base64.b64decode(email_data)
        msg = email.message_from_bytes(raw, policy=email.policy.default)

        parts = []
        sender = msg.get("From", "")
        subject = msg.get("Subject", "")
        parts.append(f"From: {sender}\nSubject: {subject}\n")

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    parts.append(part.get_content())
                elif content_type == "text/html":
                    from bs4 import BeautifulSoup
                    html = part.get_content()
                    text = BeautifulSoup(html, "lxml").get_text(separator="\n")
                    parts.append(text)
                elif content_type == "application/pdf":
                    parts.append("[PDF ATTACHMENT - will be parsed separately]")
        else:
            parts.append(msg.get_content())

        return "\n".join(parts)

    except Exception as e:
        logger.error("email_parse_error", error=str(e))
        return email_data  # Fallback: return raw   