"""Notification event codes and default labels."""

EVENT_LABELS: dict[str, str] = {
    "rent.due_soon": "Loyer bientôt exigible",
    "rent.overdue": "Loyer en retard",
    "lease.expiring": "Contrat bientôt expiré",
    "repair.new": "Nouvelle réparation",
    "payment.recorded": "Paiement enregistré",
    "receipt.available": "Reçu disponible",
    "expense.created": "Dépense ajoutée",
    "document.uploaded": "Nouveau document",
    "unit.available": "Logement disponible",
    "visit.requested": "Demande de visite",
    "approval.reviewed": "Validation traitée",
    "message.received": "Nouveau message",
}

DEFAULT_EVENT_CODES = list(EVENT_LABELS.keys())
