# MedGrid — Healthcare Patient & Clinical Integration Platform

A modular healthcare platform connecting Patients, Doctors, Appointments, EMR,
Laboratory/LIMS, Billing, Reporting, and healthcare data integrations (HL7/FHIR).

This project is being built module by module. See `docs/` for module-by-module notes.

## Status

- [x] Module 1: Project Foundation + Architecture
- [x] Module 2: PostgreSQL + SQLAlchemy + Database Design
- [x] Module 3: Authentication + JWT + RBAC
- [x] Module 4: Patient Management
- [x] Module 5: Doctor + Appointment Management
- [x] Module 6: EMR / Clinical Records
- [x] Module 7: Laboratory / LIMS
- [ ] Module 8: Billing
- [ ] Module 9: HL7/FHIR Integration
- [ ] Module 10: Reporting + Analytics
- [ ] Module 11: Testing + Reliability + SQL Optimization
- [ ] Module 12: Docker + CI/CD + AWS Deployment + Documentation

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
