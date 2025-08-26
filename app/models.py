# models.py 
# SQLAlchemy ORM models for the Photo Client Manager!.
# Design goals:
# - Simple and explicit relationships for clarity.
# - Cascades where it makes sense for child rows.
# - Optional foreign keys on Invoice let you raise an invoice without a Shoot
#   or without locking it to a Package.

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, DECIMAL, Boolean,
    ForeignKey, func
)
from sqlalchemy.orm import relationship

from .db import Base


# =========================
# Clients
# =========================
class Client(Base):
    """
    A client who books shoots and receives invoices.

    Relationships:
      - shoots: all shoots for this client
      - invoices: all invoices raised for this client
    """
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    name      = Column(String(120), nullable=False)
    email     = Column(String(255), nullable=False, unique=True, index=True)  # unique to avoid duplicates
    phone     = Column(String(50), nullable=True)

    shoots   = relationship("Shoot",   back_populates="client",  cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client",  cascade="all, delete-orphan")


# =========================
# Shoots
# =========================
class Shoot(Base):
    """
    A booked shoot for a client, with a date and optional location.

    Relationships:
      - client: owning client
      - invoices: any invoices that reference this shoot
    """
    __tablename__ = "shoots"

    shoot_id  = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id", ondelete="RESTRICT"), nullable=False)
    shoot_date = Column(Date, nullable=False)
    location   = Column(String(255), nullable=True)

    client   = relationship("Client", back_populates="shoots")
    invoices = relationship("Invoice", back_populates="shoot")


# =========================
# Packages
# =========================
class Package(Base):
    """
    A priced package option to keep quoting and invoicing consistent.

    Relationships:
      - invoices: invoices that selected this package (optional on Invoice)
    """
    __tablename__ = "packages"

    package_id  = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False, unique=True)  # unique by name to avoid duplicates
    description = Column(String(255), nullable=True)
    price       = Column(DECIMAL(10, 2), nullable=False)
    is_active   = Column(Boolean, nullable=False, default=True)

    invoices = relationship("Invoice", back_populates="package")


# =========================
# Invoices
# =========================
class Invoice(Base):
    """
    An invoice issued to a client optionally linked to a shoot and/or package.

    Relationships:
      - client: the billed client
      - shoot: optional shoot reference
      - package: optional package reference 
      - payments: all payments applied to this invoice
    """
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, index=True)

    client_id  = Column(Integer, ForeignKey("clients.client_id",  ondelete="RESTRICT"), nullable=False)
    shoot_id   = Column(Integer, ForeignKey("shoots.shoot_id",    ondelete="SET NULL"), nullable=True)
    package_id = Column(Integer, ForeignKey("packages.package_id",ondelete="SET NULL"), nullable=True)

    amount      = Column(DECIMAL(10, 2), nullable=False)  # total amount owed for this invoice
    status      = Column(String(20), nullable=False, default="draft")  # e.g. draft, sent, paid, void
    issued_date = Column(Date, nullable=False)
    due_date    = Column(Date, nullable=True)

    client  = relationship("Client",   back_populates="invoices")
    shoot   = relationship("Shoot",    back_populates="invoices")
    package = relationship("Package",  back_populates="invoices")

    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


# =========================
# Payments
# =========================
class Payment(Base):
    """
    A payment applied to a specific invoice.

    Notes:
      - paid_at defaults to server time. The API allows you to override if needed.
    """
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id", ondelete="CASCADE"), nullable=False)
    amount     = Column(DECIMAL(10, 2), nullable=False)
    method     = Column(String(50), nullable=True)  # card, bank, cash
    paid_at    = Column(DateTime, nullable=False, server_default=func.now())

    invoice = relationship("Invoice", back_populates="payments")
