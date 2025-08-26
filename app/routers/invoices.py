# app/routers/invoices.py
"""
Invoices API endpoints.

This router covers full CRUD and simple reporting helpers:
- Create an invoice with client_id, optional shoot_id and package_id
- List invoices with pagination and optional date range filters
- Get one invoice
- Update selected fields
- Delete an invoice
- Get a quick summary for totals and balance

Notes:
- Validation rules for overpayment are enforced at the Payments router,
  where totals are checked against the invoice amount.
- Date filters help with reporting windows for the assessment brief.
- Package link is optional so you can invoice ad hoc work.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import get_db
from .. import models, schemas

router = APIRouter()


def _get_invoice_or_404(db: Session, invoice_id: int) -> models.Invoice:
    """Fetch an invoice or return 404 if it does not exist."""
    obj = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return obj


@router.post("", response_model=schemas.InvoiceOut, status_code=status.HTTP_201_CREATED, summary="Create an invoice")
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    """
    Create a new invoice.

    We verify the client exists. shoot_id and package_id are optional.
    """
    # Confirm client exists
    client = db.query(models.Client).filter(models.Client.client_id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client does not exist")

    # Optional check if shoot is provided
    if payload.shoot_id is not None:
        shoot = db.query(models.Shoot).filter(models.Shoot.shoot_id == payload.shoot_id).first()
        if not shoot:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shoot does not exist")

    # Optional check if package is provided
    if payload.package_id is not None:
        package = db.query(models.Package).filter(models.Package.package_id == payload.package_id).first()
        if not package:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Package does not exist")

    invoice = models.Invoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("", response_model=list[schemas.InvoiceOut], summary="List invoices")
def list_invoices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    date_from: Optional[date] = Query(None, description="Filter invoices issued on or after this date"),
    date_to: Optional[date] = Query(None, description="Filter invoices issued on or before this date"),
    db: Session = Depends(get_db),
):
    """
    Paginated list of invoices with optional date filtering.

    Date filtering applies to issued_date. Handy for quick reporting.
    """
    q = db.query(models.Invoice)

    if date_from:
        q = q.filter(models.Invoice.issued_date >= date_from)
    if date_to:
        q = q.filter(models.Invoice.issued_date <= date_to)

    return (
        q.order_by(models.Invoice.issued_date.desc(), models.Invoice.invoice_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut, summary="Get an invoice by id")
def get_invoice(invoice_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Return one invoice by id."""
    return _get_invoice_or_404(db, invoice_id)


@router.put("/{invoice_id}", response_model=schemas.InvoiceOut, summary="Update an invoice")
def update_invoice(
    invoice_id: int = Path(..., ge=1),
    payload: schemas.InvoiceUpdate = ...,
    db: Session = Depends(get_db),
):
    """
    Patch style update for an invoice.

    If package_id or shoot_id are provided in the update, confirm they exist.
    """
    invoice = _get_invoice_or_404(db, invoice_id)
    data = payload.model_dump(exclude_unset=True)

    # Validate foreign keys if provided
    if "shoot_id" in data and data["shoot_id"] is not None:
        exists = db.query(models.Shoot).filter(models.Shoot.shoot_id == data["shoot_id"]).first()
        if not exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shoot does not exist")

    if "package_id" in data and data["package_id"] is not None:
        exists = db.query(models.Package).filter(models.Package.package_id == data["package_id"]).first()
        if not exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Package does not exist")

    for field, value in data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an invoice")
def delete_invoice(invoice_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Delete an invoice.

    Will fail if your DB is configured to restrict deletes that have payments.
    """
    invoice = _get_invoice_or_404(db, invoice_id)
    db.delete(invoice)
    db.commit()
    return None


# ---------- Helpers ----------

@router.get("/{invoice_id}/summary", response_model=schemas.InvoiceSummary, summary="Get totals and balance for an invoice")
def get_invoice_summary(invoice_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Return totals and simple balance for a single invoice.

    This is used by the UI and also referenced by the reports.
    """
    invoice = _get_invoice_or_404(db, invoice_id)

    total_paid: Decimal = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.invoice_id == invoice.invoice_id)
        .scalar()
    )

    balance = Decimal(invoice.amount) - Decimal(total_paid)
    status = (
        "paid" if balance == 0
        else "partial" if 0 < total_paid < invoice.amount
        else "unpaid"
    )

    return schemas.InvoiceSummary(
        invoice_id=invoice.invoice_id,
        amount=invoice.amount,
        total_paid=total_paid,
        balance=balance,
        status=status,
    )
