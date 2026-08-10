from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.appointments import router as appointments_router
from app.api.auth import router as auth_router
from app.api.doctors import router as doctors_router
from app.api.encounters import router as encounters_router
from app.api.fhir_integration import router as fhir_integration_router
from app.api.health import router as health_router
from app.api.invoices import router as invoices_router
from app.api.lab_orders import router as lab_orders_router
from app.api.lab_tests import router as lab_tests_router
from app.api.patients import router as patients_router
from app.api.payments import router as payments_router
from app.api.reports import router as reports_router
from app.api.test_protected import router as test_protected_router
from app.config import settings
from app.error_handling import (
    http_exception_handler,
    sqlalchemy_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.logging_config import configure_logging

configure_logging(settings.environment)

app = FastAPI(title=settings.app_name)

# Order doesn't matter here - Starlette dispatches by exact exception type
# (falling back through the MRO), so the more specific handlers
# (HTTPException, RequestValidationError, SQLAlchemyError) always win over
# the generic Exception catch-all below, regardless of registration order.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS: see explanation below - required for the browser-based React
# frontend (a different origin) to be allowed to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(appointments_router)
app.include_router(encounters_router)
app.include_router(lab_tests_router)
app.include_router(lab_orders_router)
app.include_router(invoices_router)
app.include_router(payments_router)
app.include_router(fhir_integration_router)
app.include_router(reports_router)
app.include_router(test_protected_router)
