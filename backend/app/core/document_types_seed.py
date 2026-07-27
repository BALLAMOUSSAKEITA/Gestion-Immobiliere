import uuid

DOCUMENT_TYPE_SEED: list[dict[str, str | uuid.UUID]] = [
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000201"), "code": "lease_contract", "label": "Contrat de location"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000202"), "code": "id_document", "label": "Pièce d'identité"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000203"), "code": "receipt", "label": "Reçu / Quittance"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000204"), "code": "payment_proof", "label": "Preuve de paiement"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000205"), "code": "inventory_in", "label": "État des lieux entrée"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000206"), "code": "inventory_out", "label": "État des lieux sortie"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000207"), "code": "unit_photo", "label": "Photo logement"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000208"), "code": "work_invoice", "label": "Facture travaux"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000209"), "code": "property_deed", "label": "Document de propriété"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000210"), "code": "notice_letter", "label": "Lettre de préavis"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000211"), "code": "warning", "label": "Avertissement"},
    {"id": uuid.UUID("00000000-0000-4000-8000-000000000212"), "code": "other", "label": "Autre"},
]

LEASE_CONTRACT_TYPE_ID = DOCUMENT_TYPE_SEED[0]["id"]
