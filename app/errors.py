from fastapi import HTTPException, status

# This module defines custom error responses and exceptions used in the API.
# Keeping errors centralised makes them easier to manage and update.

def client_not_found():
    """
    Raised when a client is not found in the database.
    Returns a 404 HTTP response with a simple message.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Client not found."
    )

def package_not_found():
    """
    Raised when a requested package cannot be found.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Package not found."
    )

def invoice_not_found():
    """
    Raised when an invoice with the given ID does not exist.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Invoice not found."
    )

def payment_not_found():
    """
    Raised when a payment is not found in the database.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Payment not found."
    )

def shoot_not_found():
    """
    Raised when a photo shoot record cannot be found.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Shoot not found."
    )

def duplicate_email():
    """
    Raised when a new client is being created with an email address
    that already exists in the system.
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="A client with this email already exists."
    )

def invalid_request(message: str):
    """
    Raised for custom invalid request scenarios.
    Accepts a message string to make the error more descriptive.
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )
