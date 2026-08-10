# MedGrid — Healthcare Patient & Clinical Integration Platform

A modular healthcare platform connecting Patients, Doctors, Appointments, EMR,
Laboratory/LIMS, Billing, Reporting, and healthcare data integrations (HL7/FHIR).

## About

MedGrid is a full-stack healthcare platform that connects the people and
records involved in a patient's care — patients, doctors, appointments,
clinical documentation, and laboratory workflows — behind a single,
role-based access model. It's built as a realistic, production-shaped
system: a FastAPI/PostgreSQL backend with proper migrations, JWT
authentication, and layered business logic, paired with a React/TypeScript
frontend, rather than a toy CRUD demo.

## The Problem It Solves

In many small-to-mid-size healthcare settings, patient data ends up spread
across disconnected tools: one system for scheduling, another spreadsheet
for patient records, paper or PDF lab reports, and no single source of
truth for a patient's clinical history. That fragmentation creates real
problems:

- **No unified patient record** — a doctor can't easily see a patient's
  full history (past visits, diagnoses, lab results) in one place.
- **Weak or absent access control** — front-desk staff, doctors, lab
  technicians, and billing staff often end up with the same broad access
  to systems, when their actual jobs require very different views into
  the same data.
- **No audit trail** — clinical notes and lab results get edited in place
  in spreadsheets or shared documents, with no record of who changed what,
  when.
- **Manual, error-prone lab workflows** — test orders, pending queues, and
  results tracked by hand instead of through a system that enforces
  status transitions and catches double-bookings or conflicting orders.

MedGrid addresses this by modeling each of these concerns as a proper,
related set of database entities (patients, doctors, appointments,
encounters, clinical records, lab orders/results) with:

- **Role-based access control** tailored per resource — e.g. billing staff
  can see that a lab test was ordered without seeing the clinical result;
  only doctors can author diagnoses.
- **A real, append-only audit trail** for clinical documentation, so
  records are corrected by addition, never silent edits.
- **Enforced business rules at the database level** (not just the API),
  like preventing a doctor or patient from being double-booked, using
  atomic constraints rather than best-effort application checks.
- **A clean integration boundary** for external lab systems (LIMS),
  simulated for now but built so a real integration can be swapped in
  without touching the rest of the codebase.

## Architecture

```
React + TypeScript  --HTTP/JSON-->  FastAPI  --SQL-->  PostgreSQL
                                       |
                          api/ -> services/ -> database/
```

## Running the backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Docs available at http://localhost:8000/docs

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```


## Credentials

```bash
Usernaem = admin@example.com
Password = YourStrongPassword123
```

Available at https://med-grid-two.vercel.app
