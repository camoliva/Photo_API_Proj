# app/schemas.py 
"""
Pydantic v2 schemas for request and response validation

Design notes:
- `model_config = ConfigDict(from_attributes=True)` is set on output models so
  we can return ORM objects straight from SQLAlchemy without extra mapping.
- Where it helps readability I keep fields grouped by feature area.
- Validation is kept practical. Stronger constraints are a future improvement.
- Decimal is used for money to avoid float rounding surprises!.

All field names are aligned with the API and table design for clarity.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Base config for reading from ORM instances without extra conversion code
OrmConfig = dict(from_attributes=True)

# -------------------------
# Clients
# -------------------------

class ClientBase(BaseModel):
    """Core client attributes shared by create and read operations."""
    name: str
    email: EmailStr
    phone: Optional[str] = None  # keep simple for now; can add a stricter pattern later

class ClientCreate(ClientBase):
    """Payload for creating a client."""
    pass

class ClientUpdate(BaseModel):
    """Patch-style update. Only provided fields will be changed."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ClientOut(ClientBase):
    """Response model for returning a client record."""
    model_config = ConfigDict(**OrmConfig)
    client_id: int


# -------------------------
# Shoots
# -------------------------

class ShootBase(BaseModel):
    """Minimal fields required to represent a shoot."""
    client_id: int
    shoot_date: date
    location: Optional[str] = None

class ShootCreate(ShootBase):
    """Payload for creating a shoot."""
    pass

class ShootUpdate(BaseModel):
    """Patch-style update for a shoot."""
    shoot_date: Optional[date] = None
    location: Optional[str] = None

class ShootOut(ShootBase):
    """Response model for returning a shoot record."""
    model_config = ConfigDict(**OrmConfig)
    shoot_id: int


# -------------------------
# Packages
# -------------------------

class PackageBase(BaseModel):
    """
    Package information used on invoices.
    using decimal for price so money maths is predictable.
    """
    name: str
    description: Optional[str] = None
    price: Decimal
    is_active: bool = True

class PackageCreate(PackageBase):
    """Payload for creating a package."""
    pass

class PackageUpdate(BaseModel):
    """Patch-style update for package details."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class PackageOut(PackageBase):
    """Response model for returning a package record."""
    model_config = ConfigDict(**OrmConfig)
    package_id: int


# -------------------------
# Invoices
# -------------------------

class InvoiceBase(BaseModel):
    """
    Invoice basics package and shoot are optional so you can invoice
    simple work without tying it to a shoot or package.
    """
    client_id: int
    amount: Decimal
    issued_date: date
    status: str = "draft"
    due_date: Optional[date] = None
    shoot_id: Optional[int] = None
    package_id: Optional[int] = None

class InvoiceCreate(InvoiceBase):
    """Payload for creating an invoice."""
    pass

class InvoiceUpdate(BaseModel):
    """
    Patch style update for invoicing, helpful during draft stage or when
    recording status changes.
    """
    amount: Optional[Decimal] = None
    status: Optional[str] = None
    issued_date: Optional[date] = None
    due_date: Optional[date] = None
    shoot_id: Optional[int] = None
    package_id: Optional[int] = None

class InvoiceOut(InvoiceBase):
    """Response model for returning an invoice record."""
    model_config = ConfigDict(**OrmConfig)
    invoice_id: int


# -------------------------
# Payments
# -------------------------

class PaymentBase(BaseModel):
    """Payment details recorded against an invoice."""
    invoice_id: int
    amount: Decimal
    method: Optional[str] = None  # eg card, bank, cash
    paid_at: Optional[datetime] = None  # server will return ISO string

class PaymentCreate(PaymentBase):
    """Payload for creating a payment."""
    pass

class PaymentOut(PaymentBase):
    """Response model for returning a payment record."""
    model_config = ConfigDict(**OrmConfig)
    payment_id: int


# -------------------------
# Invoice summary
# -------------------------

class InvoiceSummary(BaseModel):
    """
    view for totals used in the summary endpoint.
    This keeps the client UI simple when it only needs money figures.
    """
    invoice_id: int
    amount: Decimal
    total_paid: Decimal
    balance: Decimal
    status: str


# -------------------------
# Reports
# -------------------------
# modified from feedback (show all the key fields in one row)

class ReportInvoiceRow(BaseModel):
    """
    Row format for /reports/invoices.
    Fields are named to read well in Swagger and CSV.
    """
    client_name: str
    package_name: Optional[str] = None
    invoice_amount: Decimal
    total_paid: Decimal
    balance: Decimal
    shoot_location: Optional[str] = None
    payment_status: str        # unpaid, partial, or paid
    invoice_id: int
    issued_date: date
