"""Codes d'actions nécessitant validation super admin."""

PAYMENT_DELETE = "payment.delete"
PAYMENT_UPDATE_AMOUNT = "payment.update_amount"
TENANT_DELETE = "tenant.delete"
BUILDING_CHANGE_OWNER = "building.change_owner"
LEASE_UPDATE = "lease.update"
EXPENSE_VALIDATE = "expense.validate"
RECEIPT_CANCEL = "receipt.cancel"
DOCUMENT_DELETE = "document.delete"

SENSITIVE_ACTIONS = {
    PAYMENT_DELETE,
    PAYMENT_UPDATE_AMOUNT,
    TENANT_DELETE,
    BUILDING_CHANGE_OWNER,
    LEASE_UPDATE,
    EXPENSE_VALIDATE,
    RECEIPT_CANCEL,
    DOCUMENT_DELETE,
}
