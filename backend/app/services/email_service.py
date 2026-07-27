import logging
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import EmailQueueStatus
from app.models.notification import EmailQueue

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"


class EmailService:
    MAX_ATTEMPTS = 3

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self._jinja = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_template(self, template_name: str, context: dict) -> str:
        template = self._jinja.get_template(template_name)
        return template.render(**context, agency_name=self.settings.agency_name)

    def enqueue(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachments: dict | None = None,
        scheduled_at: datetime | None = None,
    ) -> EmailQueue:
        item = EmailQueue(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            attachments=attachments,
            scheduled_at=scheduled_at or datetime.now(UTC),
        )
        self.db.add(item)
        self.db.flush()
        return item

    def process_queue(self, batch_size: int = 20) -> int:
        now = datetime.now(UTC)
        pending = (
            self.db.query(EmailQueue)
            .filter(
                EmailQueue.status == EmailQueueStatus.pending,
                EmailQueue.scheduled_at <= now,
            )
            .order_by(EmailQueue.scheduled_at.asc())
            .limit(batch_size)
            .all()
        )
        processed = 0
        for item in pending:
            if self._send_item(item):
                processed += 1
        if processed:
            self.db.commit()
        return processed

    def _send_item(self, item: EmailQueue) -> bool:
        item.attempts += 1
        try:
            if self.settings.smtp_host:
                self._send_smtp(item.to_email, item.subject, item.body_html)
            else:
                logger.info(
                    "Email simulé → %s | %s",
                    item.to_email,
                    item.subject,
                )
            item.status = EmailQueueStatus.sent
            item.sent_at = datetime.now(UTC)
            item.last_error = None
            return True
        except Exception as exc:  # noqa: BLE001
            item.last_error = str(exc)
            if item.attempts >= self.MAX_ATTEMPTS:
                item.status = EmailQueueStatus.failed
            logger.exception("Échec envoi email %s", item.id)
            return False

    def _send_smtp(self, to_email: str, subject: str, body_html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.smtp_from_email
        msg["To"] = to_email
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            if self.settings.smtp_use_tls:
                server.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.sendmail(self.settings.smtp_from_email, [to_email], msg.as_string())
