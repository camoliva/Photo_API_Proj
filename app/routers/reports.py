# app/routers/reports.py 
"""
Reports endpoints.
This router exposes a joined report for invoices so you can see the bigger picture:
- /reports/invoices gives client name, package name, totals, balance and status
- supports optional date range filtering on issued_date

Notes:
- This is read only no writes here.
- Keep joins simple and indexed to stay quick on MySQL.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter()


@router.get("/invoices", response_model=list[schemas.ReportInvoiceRow], summary="Invoice report with balances")
def report_invoices(
    date_from: Optional[date] = Query(None, description="Filter invoices issued on or after this date"),
    date_to: Optional[date] = Query(None, description="Filter invoices issued on or before this date"),
    db: Session = Depends(get_db),
):
    """
    Combined view of invoices, clients, packages and payments.

    Fields returned:
    - invoice_id, issued_date, due_date
    - client_name
    - package_name
    - amount, total_paid, balance
    - status: unpaid, partial, or paid
    """
    inv = models.Invoice
    cli = models.Client
    pkg = models.Package
    pay = models.Payment

    # base query with joins to client and package
    q = (
        db.query(
            inv.invoice_id.label("invoice_id"),
            inv.issued_date.label("issued_date"),
            inv.due_date.label("due_date"),
            cli.name.label("client_name"),
            pkg.name.label("package_name"),
            inv.amount.label("amount"),
            func.coalesce(func.sum(pay.amount), 0).label("total_paid"),
        )
        .join(cli, cli.client_id == inv.client_id)
        .outerjoin(pkg, pkg.package_id == inv.package_id)
        .outerjoin(pay, pay.invoice_id == inv.invoice_id)
        .group_by(
            inv.invoice_id, inv.issued_date, inv.due_date,
            cli.name, pkg.name, inv.amount
        )
        .order_by(inv.issued_date.desc(), inv.invoice_id.desc())
    )

    # optional issued_date filtering
    if date_from:
        q = q.filter(inv.issued_date >= date_from)
    if date_to:
        q = q.filter(inv.issued_date <= date_to)

    rows = q.all()

    # map DB rows to schema objects with balance + status
    results: list[schemas.ReportInvoiceRow] = []
    for r in rows:
        total_paid = Decimal(r.total_paid or 0)
        amount = Decimal(r.amount or 0)
        balance = amount - total_paid

        if balance == 0:
            status = "paid"
        elif 0 < total_paid < amount:
            status = "partial"
        else:
            status = "unpaid"

        results.append(
            schemas.ReportInvoiceRow(
                invoice_id=r.invoice_id,
                issued_date=r.issued_date,
                due_date=r.due_date,
                client_name=r.client_name,
                package_name=r.package_name,
                amount=amount,
                total_paid=total_paid,
                balance=balance,
                status=status,
            )
        )

    return results
