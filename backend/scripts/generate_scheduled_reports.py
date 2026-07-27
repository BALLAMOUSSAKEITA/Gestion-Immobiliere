"""Generate scheduled reports (cron entrypoint).

Usage examples:
  python -m scripts.generate_scheduled_reports daily
  python -m scripts.generate_scheduled_reports weekly
  python -m scripts.generate_scheduled_reports monthly
  python -m scripts.generate_scheduled_reports annual
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from app.core.database import SessionLocal
from app.models.enums import ReportType
from app.services.report_service import ReportService


def _period_for(report_type: str) -> tuple[date, date]:
    today = date.today()
    if report_type == "daily":
        return today, today
    if report_type == "weekly":
        start = today - timedelta(days=today.weekday())
        return start, today
    if report_type == "monthly":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(day=31)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end
    if report_type == "annual":
        return today.replace(month=1, day=1), today.replace(month=12, day=31)
    raise ValueError(f"Type inconnu: {report_type}")


def main() -> None:
    report_type = sys.argv[1] if len(sys.argv) > 1 else "monthly"
    period_start, period_end = _period_for(report_type)
    db = SessionLocal()
    try:
        ReportService(db).generate_scheduled(
            ReportType(report_type),
            period_start,
            period_end,
        )
        print(f"Rapport {report_type} généré pour {period_start} → {period_end}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
