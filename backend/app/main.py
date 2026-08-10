from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.appointments import router as appointments_router
from app.api.auth import router as auth_router
from app.api.doctors import router as doctors_router
from app.api.encounters import router as encounters_router
from app.api.health import router as health_router
from app.api.lab_orders import router as lab_orders_router
from app.api.lab_tests import router as lab_tests_router
from app.api.patients import router as patients_router
from app.api.test_protected import router as test_protected_router
from app.config import settings

app = FastAPI(title=settings.app_name)

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
app.include_router(test_protected_router)
