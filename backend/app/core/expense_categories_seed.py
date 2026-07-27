import uuid

EXPENSE_CATEGORY_SEED: list[dict[str, str | uuid.UUID]] = [
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000101"), "code": "repair", "label": "Réparation"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000102"), "code": "painting", "label": "Peinture"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000103"), "code": "plumbing", "label": "Plomberie"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000104"), "code": "electricity", "label": "Électricité"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000105"), "code": "security", "label": "Gardiennage"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000106"), "code": "cleaning", "label": "Nettoyage"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000107"), "code": "taxes", "label": "Taxes"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000108"), "code": "supplies", "label": "Fournitures"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000109"), "code": "construction", "label": "Travaux / Gros œuvre"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000110"), "code": "other", "label": "Autre"},
]
