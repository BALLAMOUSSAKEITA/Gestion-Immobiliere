import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.enums import LeaseStatus, RentPeriodStatus
from app.models.payment import RentPeriod
from app.models.tenant import Lease, Tenant
from app.services.email_service import EmailService
from app.services.notification_hooks import notify_lease_expiring, notify_rent_due_soon

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def process_email_queue() -> None:
    db = SessionLocal()
    try:
        processed = EmailService(db).process_queue()
        if processed:
            logger.info("Emails traités : %s", processed)
    except Exception:  # noqa: BLE001
        logger.exception("Erreur traitement email queue")
        db.rollback()
    finally:
        db.close()


def send_rent_reminders() -> None:
    db = SessionLocal()
    try:
        today = date.today()
        soon = today + timedelta(days=3)
        periods = (
            db.query(RentPeriod)
            .join(Lease)
            .options(joinedload(RentPeriod.lease).joinedload(Lease.tenant), joinedload(RentPeriod.lease).joinedload(Lease.unit))
            .filter(
                RentPeriod.due_date == soon,
                RentPeriod.status != RentPeriodStatus.paid,
                Lease.status == LeaseStatus.active,
            )
            .all()
        )
        for period in periods:
            lease = period.lease
            if lease is None or lease.tenant is None or lease.unit is None:
                continue
            amount = f"{period.expected_amount - period.paid_amount:,.0f}".replace(",", " ")
            notify_rent_due_soon(
                db,
                lease.tenant,
                lease.unit.code,
                amount,
                period.due_date.isoformat(),
            )

        expiring = (
            db.query(Lease)
            .options(joinedload(Lease.tenant), joinedload(Lease.unit))
            .filter(
                Lease.status == LeaseStatus.active,
                Lease.end_date.isnot(None),
                Lease.end_date <= today + timedelta(days=30),
                Lease.end_date >= today,
            )
            .all()
        )
        for lease in expiring:
            if lease.tenant and lease.unit and lease.end_date:
                notify_lease_expiring(
                    db,
                    f"{lease.tenant.first_name} {lease.tenant.last_name}",
                    lease.unit.code,
                    lease.end_date.isoformat(),
                )
    except Exception:  # noqa: BLE001
        logger.exception("Erreur rappels loyer")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(process_email_queue, "interval", seconds=30, id="email_queue")
    scheduler.add_job(send_rent_reminders, "cron", hour=8, minute=0, id="rent_reminders")
    scheduler.start()
    logger.info("Scheduler démarré")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@asynccontextmanager
async def lifespan(app):  # noqa: ARG001
    start_scheduler()
    yield
    stop_scheduler()
