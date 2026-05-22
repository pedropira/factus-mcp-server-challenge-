"""
Service layer — business logic consuming FactusClient and/or repositories.

Factus API services (requieren FactusClient):
  - InvoiceService           — facturas electrónicas (POST/GET /v2/bills)
  - CreditNoteService        — notas crédito (POST/GET /v2/credit-notes)
  - CompanyService           — información empresa (GET /v2/companies)
  - SupportDocumentService   — documentos soporte (POST/GET/DELETE /v2/support-documents)
  - AdjustmentNoteService    — notas de ajuste (POST/GET/DELETE /v2/support-document-adjustment-notes)

Local DB services (requieren AsyncSession):
  - CustomerService          — CRUD clientes locales
  - EstablishmentService     — CRUD establecimientos locales
  - NumberingRangeService    — rangos de numeración (local + Factus API)
  - ProductService           — CRUD productos locales
"""

from src.services.adjustment_note_service import AdjustmentNoteService
from src.services.company_service import CompanyService
from src.services.credit_note_service import CreditNoteService
from src.services.customer_service import CustomerService
from src.services.establishment_service import EstablishmentService
from src.services.invoice_service import FactusApiError, InvoiceService
from src.services.numbering_range_service import NumberingRangeService
from src.services.product_service import ProductService
from src.services.support_document_service import SupportDocumentService

__all__ = [
    "AdjustmentNoteService",
    "CompanyService",
    "CreditNoteService",
    "CustomerService",
    "EstablishmentService",
    "FactusApiError",
    "InvoiceService",
    "NumberingRangeService",
    "ProductService",
    "SupportDocumentService",
]
