# main.py 
''' 
FastAPI application bootstrap for the Photo Client Manager API.
Notes:
- Creates tables on startup for a simple, migration free workflow in class.
- Registers all routers that are part of the current scope of the project.
'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine, Base
from .routers import clients, shoots, packages, invoices, payments, reports

# Create DB tables if they do not exist yet.
Base.metadata.create_all(bind=engine)

# App metadata shows up in Swagger UI.
app = FastAPI(title="Photo Client Manager API")

# CORS: wide open for local testing tools and front-end experiments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev-friendly will lock down later
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
Routers (photographers and shoot_photographer were intentionally removed to keep the scope manageable)
Each router sticks to one concern so the API surface stays tidy.
'''
app.include_router(clients.router,   prefix="/clients",   tags=["clients"])
app.include_router(shoots.router,    prefix="/shoots",    tags=["shoots"])
app.include_router(packages.router,  prefix="/packages",  tags=["packages"])
app.include_router(invoices.router,  prefix="/invoices",  tags=["invoices"])
app.include_router(payments.router,  prefix="/payments",  tags=["payments"])
app.include_router(reports.router,   prefix="/reports",   tags=["reports"])

@app.get("/", tags=["health"])
def root():
    """Simple readiness check for quick smoke tests."""
    return {"ok": True, "service": "photo_api_v3"}
