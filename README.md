# MedGrid — Healthcare Patient & Clinical Integration Platform

A full-stack, production-shaped healthcare platform connecting Patients,
Doctors, Appointments, EMR/Clinical Records, Laboratory/LIMS, Billing,
Reporting & Analytics, and simulated HL7/FHIR healthcare-system
interoperability — built module by module, with tests and real
measurements backing every claim in this document.

**Live demo:** https://med-grid-two.vercel.app
```
Username: admin@example.com
Password: YourStrongPassword123
```

---

## 1. Project Overview

MedGrid connects the people and records involved in a patient's care —
patients, doctors, appointments, clinical documentation, and laboratory
workflows — behind a single, role-based access model.

**The problem it addresses:** in many small-to-mid-size healthcare
settings, patient data is spread across disconnected tools — one system
for scheduling, a spreadsheet for records, paper lab reports — with no
single source of truth, weak access control (front-desk staff, doctors,
lab techs, and billing staff often get the same broad access despite
needing very different views), no audit trail on clinical notes, and
manual, error-prone lab/billing workflows. MedGrid models each of these
as a proper relational schema with role-scoped access, an append-only
clinical audit trail, and business rules enforced at the database level
(atomic constraints), not just best-effort application checks.

## 2. Architecture

```
React + TypeScript  --HTTP/JSON-->  FastAPI  --SQL-->  PostgreSQL
                                       │
                          api/ -> services/ -> database/
                                       │
                            integrations/ (lims, payment_gateway,
                                           fhir, health_exchange)
```

**Backend layering** (enforced throughout, not just at the top level):
`api/` routes only translate HTTP ↔ Python and never contain business
logic; `services/` hold all business rules and own the transaction
boundary; `database/` is the SQLAlchemy engine/session layer;
`integrations/` isolates every external-system dependency (real or
simulated) behind a swappable interface, so the rest of the app never
depends on a concrete implementation.

**Frontend structure:** one directory per domain (`patients/`, `doctors/`,
`appointments/`, `encounters/`, `labs/`, `billing/`, `reports/`), a shared
`lib/api.ts` client, and a `AuthContext` handling the JWT lifecycle.

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router, Recharts |
| Backend | Python, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Auth | JWT (PyJWT), Argon2id password hashing (argon2-cffi) |
| Testing | pytest, httpx (FastAPI TestClient) |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |
| Deployed on | Render (backend), Vercel (frontend), Neon (Postgres) |

## 4. Features

- **Patient management** — CRUD, search, pagination, server-generated
  patient numbers (via a Postgres `SEQUENCE`, race-safe under concurrency).
- **Doctor & appointment scheduling** — conflict-free booking enforced by
  partial unique indexes (not just application checks), status lifecycle
  (`SCHEDULED → COMPLETED/CANCELLED/NO_SHOW`).
- **EMR / clinical records** — `Encounter` (the clinical substance of a
  visit) kept separate from `Appointment` (the scheduling fact), with an
  append-only `ClinicalRecord` audit trail — corrections are added, never
  edited in place.
- **Laboratory / LIMS** — test catalog, order → pending queue → simulated
  external LIMS processing, with real retry/failure handling.
- **Billing** — invoices with derived (never directly-set) status,
  multiple payments per invoice, a simulated payment gateway with the
  same retry/failure pattern as the lab integration.
- **HL7/FHIR integration layer** — internal models mapped to minimal,
  honest FHIR-shaped resources and transmitted to a simulated external
  health exchange.
- **Reporting & analytics** — five hand-written-SQL reporting endpoints
  and a Recharts dashboard.
- **Role-based access control** — five roles (`ADMIN`, `DOCTOR`, `PATIENT`,
  `LAB_TECHNICIAN`, `BILLING_STAFF`), each scoped per-resource rather than
  globally (e.g. billing staff can see that a lab test was ordered without
  seeing the clinical result).

## 5. Database Schema

11 tables, evolved across modules via reviewed Alembic migrations (never
hand-edited in place):

| Table | Purpose | Key relationships |
|---|---|---|
| `users` | Login identity + role | — |
| `patients` | Demographics | — |
| `doctors` | Staff directory | — |
| `appointments` | Scheduling | `patient_id`, `doctor_id` |
| `encounters` | Clinical visit substance | `patient_id`, `doctor_id`, optional unique `appointment_id` (1:1) |
| `clinical_records` | Append-only clinical notes | `encounter_id`, `created_by_user_id` |
| `lab_tests` | Test catalog | — |
| `lab_orders` | Ordered tests | `patient_id`, `doctor_id`, `test_id` |
| `lab_results` | Completed results | unique `lab_order_id` (1:1) |
| `invoices` | Billing claims | `patient_id`, optional `appointment_id` |
| `payments` | Payment attempts | `invoice_id` (1:many), `recorded_by_user_id` |

Relationship patterns used deliberately, not interchangeably: plain
one-to-many (`Patient → Appointment`), true one-to-one (`Appointment ↔
Encounter`, `LabOrder ↔ LabResult` — optional and unique), and genuine
one-to-many where multiple attempts matter (`Invoice → Payment`).

## 6. API Documentation

Full interactive documentation (request/response schemas, try-it-out) is
auto-generated by FastAPI at **`/docs`** on the running backend. Route
groups:

`/auth`, `/patients`, `/doctors`, `/appointments`, `/encounters`,
`/lab-tests`, `/lab-orders`, `/invoices`, `/payments`,
`/integrations/fhir`, `/reports`, `/health`.

## 7. Authentication

JWT-based (HS256, `PyJWT`), passwords hashed with **Argon2id**
(`argon2-cffi`, used directly rather than through the unmaintained
`passlib`). `POST /auth/register` → `POST /auth/login` (OAuth2 password
flow — form-encoded, works with Swagger's "Authorize" button) →
`Authorization: Bearer <token>` on every subsequent request. Five roles,
each with resource-specific permissions rather than a single global
"admin vs. everyone" split — e.g. `DOCTOR` and `ADMIN` can both manage
patients, but only `DOCTOR` can author clinical encounters, and only
`ADMIN`/`BILLING_STAFF` touch billing.

**A known, deliberately-flagged limitation:** there is currently no link
from a logged-in `PATIENT` user to "their own" `Patient` record, so
patient self-service (seeing only your own appointments/results) isn't
implemented — the `PATIENT` role exists and authenticates, but is
excluded from most clinical/billing endpoints for exactly this reason.
See Future Improvements.

## 8. Healthcare Integration (HL7/FHIR)

`app/integrations/fhir/` maps three internal models to minimal,
illustrative FHIR resources (`Patient`, `Encounter`, `Observation`) — not
a certified or spec-complete HL7/FHIR implementation, by design. The
mapping layer (data *shape*) and `app/integrations/health_exchange/`
(data *transport*) are deliberately separate concerns. `/integrations/fhir/*`
endpoints demonstrate: mapping in isolation (`GET`), and the full
mapper → transmit → retry pipeline (`POST .../export`), with a
deterministic test hook to reproduce `SUCCESS`, `RETRY`, and `FAILED`
outcomes on demand.

## 9. LIMS Simulation

`app/integrations/lims/` — a `LimsClient` interface with a
`SimulatedLimsClient` implementation (realistic latency, a real random
failure rate). The rest of the app depends only on the interface, so a
real LIMS integration could replace the simulation by writing one new
class and changing one factory function — no other file would need to
change. The same abstraction pattern is reused for the payment gateway
(Module 8) and the health exchange (Module 9).

## 10. Testing

`backend/tests/`, organized to make the unit/integration/API distinction
visible in the folder structure itself:

```
tests/
├── unit/          pure functions, zero I/O (password hashing, FHIR mappers)
├── integration/   service functions + a real test database, no HTTP
└── api/           full HTTP requests through FastAPI's TestClient
```

40 tests, run against a dedicated `carebridge_test` Postgres database
(never the dev database), each wrapped in a transaction that's rolled
back afterward for isolation and speed. External dependencies (the
simulated LIMS client, the simulated payment gateway) are mocked in tests
that don't specifically exercise them, so the suite is fast (~2.5s) and
deterministic rather than depending on real `time.sleep()`/`random()`.

```bash
cd backend && source venv/bin/activate && python -m pytest -v
```

## 11. SQL Optimization

A real, measured example (not an invented one) — see `app/services/reporting_service.py`
and the migration `d4448748e84b`. Query: `SELECT * FROM lab_orders WHERE status = 'PENDING'`,
benchmarked against 200,000 synthetic rows (~5% matching), with
`VACUUM ANALYZE` run before each measurement:

| | Plan | Execution Time |
|---|---|---|
| Before index | `Seq Scan on lab_orders` | **27.294 ms** |
| After index | `Index Scan using ix_lab_orders_status` | **4.412 ms** |

A real ~6.2x improvement at this data volume. The synthetic benchmark
data was deleted after measurement; the index itself is permanent.

## 12. Docker

```bash
docker compose up --build
```

Three services: `frontend` (multi-stage build — Vite build artifacts
served by nginx, not the dev server), `backend` (runs Alembic migrations
then Uvicorn), `db` (Postgres 16, with a healthcheck the backend waits
on via `depends_on: condition: service_healthy`). Verified end-to-end:
container-to-container networking (`backend` reaches Postgres via the
service name `db`, not `localhost`), and a real user registered through
the Dockerized backend, independently confirmed in the Dockerized
database.

## 13. Deployment

**Currently live:** Render (backend, free tier) + Vercel (frontend) +
Neon (managed Postgres) — see the live demo link at the top of this file.

**CI:** `.github/workflows/ci.yml` — on every push/PR to `main`, runs the
full backend test suite against a real Postgres service container, and
type-checks + builds the frontend. A failing test or build fails the
workflow and blocks the merge.

**AWS (designed, not deployed — no AWS account was available while
building this):** ECS Fargate (containers, no Kubernetes, no EC2 to
manage) behind an Application Load Balancer, RDS for PostgreSQL in a
private subnet, secrets in Secrets Manager (never plaintext env vars),
Amplify Hosting for the frontend, logs streamed to CloudWatch. Full
step-by-step design covered during Module 12.

## 14. Screenshots

_Not included in this revision._ To add: run the app locally or visit the
live demo, capture the login page, patient list, appointment booking,
encounter detail, lab dashboard, billing detail, and reports dashboard,
save them under `docs/screenshots/`, and reference them here.

## 15. Future Improvements

Honest gaps, not hidden ones — each was flagged in the module where it
first became relevant:

- **Patient self-service portal** — requires a `User ↔ Patient` link that
  doesn't exist yet (flagged since Module 3); currently the `PATIENT`
  role can authenticate but not see its own data.
- **Doctor revenue attribution** — `reports/doctor-performance` computes
  revenue via `invoices.appointment_id`, but the invoice-creation UI
  never links one, so this currently always shows $0 (a real, visible
  consequence documented in Module 10, not a bug in the query).
- **Real external integrations** — the LIMS, payment gateway, and health
  exchange are all simulated by design; each has a clean interface ready
  for a real implementation to be swapped in.
- **Token revocation** — JWTs are stateless; there's no way to force-expire
  a single token before it naturally expires (a documented trade-off from
  Module 3).
- **CI does not deploy** — the pipeline tests and builds, but doesn't
  automatically push to Render/Vercel or AWS.
- **Idempotency keys** — a duplicate webhook/retry from a real payment
  gateway could double-process a payment; not yet guarded against.
- **Remove `test_protected.py`** — Module 3's temporary role-check
  endpoints were never replaced once real business endpoints existed.

## Running Locally (without Docker)

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Docs at http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# http://localhost:5173
```
