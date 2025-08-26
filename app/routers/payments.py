# app/routers/payments.py 
"""
Payments API endpoints.

this router records money paid against invoices:
- Create a payment for an invoice
- List payments with pagination
- Get one payment
- Delete a payment

Notes:
- We block overpayments to keep balances sensible.
- paid_at is stored in the DB as a datetime. Schemas format it for API output.
- Business rule: a payment cannot be zero or negative.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter()


def _get_invoice_or_404(db: Session, invoice_id: int) -> models.Invoice:
    """Fetch an invoice or 404. Used by most endpoints here."""
    obj = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return obj


def _get_payment_or_404(db: Session, payment_id: int) -> models.Payment:
    """Fetch a payment or 404."""
    obj = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return obj


@router.post("", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED, summary="Create a payment")
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db)):
    """
    Record a payment.

    Steps:
    1) confirm the invoice exists
    2) sum existing payments
    3) reject if the new total would exceed the invoice amount
    """
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")

    invoice = _get_invoice_or_404(db, payload.invoice_id)

    total_paid = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.invoice_id == invoice.invoice_id)
        .scalar()
    )
    new_total = Decimal(total_paid) + Decimal(payload.amount)

    if new_total > Decimal(invoice.amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment exceeds invoice amount"
        )

    payment = models.Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("", response_model=list[schemas.PaymentOut], summary="List payments")
def list_payments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """Simple paginated list of payments."""
    return (
        db.query(models.Payment)
        .order_by(models.Payment.payment_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{payment_id}", response_model=schemas.PaymentOut, summary="Get a payment by id")
def get_payment(payment_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Return a single payment."""
    return _get_payment_or_404(db, payment_id)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a payment")
def delete_payment(payment_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Delete a payment.

    Helpful for clean up in testing or if you entered the wrong amount.
    """
    payment = _get_payment_or_404(db, payment_id)
    db.delete(payment)
    db.commit()
    return None
