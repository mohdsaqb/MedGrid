# MedGrid — Interview Preparation

20 questions grounded strictly in what was actually built during this
project (Modules 1-12). No claimed feature or fixed bug here is
hypothetical.

---

## Architecture

### 1. Walk me through what happens, step by step, when a doctor requests `GET /patients/{id}`.

**Tests:** whether you understand your own stack's request lifecycle, not
just that it "works."

**Answer:** The request hits FastAPI's router, which resolves `GET
/patients/{patient_id}`. Before the route body runs, FastAPI resolves its
dependencies: `get_db` opens a SQLAlchemy session for this request only,
and `get_current_user` (via `Depends`) decodes the JWT from the
`Authorization` header, verifies its signature and expiry, and loads the
`User` row by the token's `sub` claim. Then `require_role(ADMIN, DOCTOR,
LAB_TECHNICIAN, BILLING_STAFF)` checks the loaded user's role and raises
`403` if it doesn't match. If all of that passes, the route function
calls `patient_service.get_patient(db, patient_id)`, which does a single
`db.get(Patient, patient_id)` and raises a `PatientNotFoundError` if
nothing's found — translated by the route into a `404`. On success, the
ORM object is serialized through the `PatientRead` Pydantic schema
(which never includes internal-only fields) and returned as JSON.

### 2. Why did you separate `Encounter` from `Appointment` instead of just adding clinical fields to the appointments table?

**Tests:** data-modeling judgment — do you default to normalizing
everything into one table, or can you justify a real separation?

**Answer:** They represent genuinely different things with different
lifecycles. `Appointment` is a scheduling fact — a slot was booked, and
it can be cancelled or no-showed without any clinical content ever
existing. `Encounter` is the clinical substance of a visit — diagnosis,
symptoms, notes — and can exist without a prior appointment at all (a
walk-in). They also need different access rules: I let `BILLING_STAFF`
read appointment data (they need to know a visit happened, for
invoicing), but excluded them entirely from encounters, because clinical
diagnosis and notes are materially more sensitive than "a slot was
booked." Mixing them into one table would have made that access split
impossible to express cleanly.

### 3. You have separate `lims/`, `payment_gateway/`, and `fhir`/`health_exchange` integration packages. Why not just call the external systems directly from your service functions?

**Tests:** understanding of dependency inversion and why it matters
beyond "it's cleaner."

**Answer:** Every one of those packages defines an abstract interface
(`LimsClient`, `PaymentGatewayClient`, `HealthExchangeClient`) with a
`Simulated*` implementation behind it, and a single factory function
(`get_lims_client()`, etc.) that decides which concrete class is active.
Services depend only on the interface. This paid off concretely in
Module 11's testing: because `lab_order_service` doesn't know or care
that it's talking to `SimulatedLimsClient`, I could substitute a fake
test double with `monkeypatch.setattr("app.services.lab_order_service.get_lims_client", ...)`
and get fast, deterministic tests with zero real network calls or
`time.sleep()`. It also means replacing the simulation with a real LIMS
integration later touches exactly one file — the factory function — not
every place that currently calls it.

---

## SQL

### 4. How would you find doctors who have never had any appointments?

**Tests:** whether you actually understand `LEFT JOIN` vs `INNER JOIN`,
not just that "left join is for optional stuff."

**Answer:**
```sql
SELECT d.id, d.name
FROM doctors d
LEFT JOIN appointments a ON a.doctor_id = d.id
WHERE a.id IS NULL;
```
An `INNER JOIN` would silently drop any doctor with zero appointments
from the result entirely, since there's no matching row on the right
side. `LEFT JOIN` keeps every doctor row and fills in `NULL`s where there's
no match — so filtering for `a.id IS NULL` gives exactly the doctors with
no appointments. This is the same reasoning behind why the
doctor-performance report joins `FROM doctors LEFT JOIN appointments`,
not the other way around.

### 5. What's the actual difference between `WHERE` and `HAVING`?

**Tests:** whether you understand SQL's logical execution order, not just
syntax.

**Answer:** `WHERE` filters individual rows *before* grouping happens —
you can't reference an aggregate like `COUNT(*)` in it because it doesn't
exist yet at that point in execution. `HAVING` filters *after*
aggregation, operating on the grouped results. A concrete example from
this project: `SELECT d.department, COUNT(DISTINCT a.patient_id) AS
patient_count FROM doctors d LEFT JOIN appointments a ON a.doctor_id =
d.id GROUP BY d.department HAVING COUNT(DISTINCT a.patient_id) > 0` — I
used `LEFT JOIN` so no department with doctors is silently dropped, then
`HAVING` to hide departments with zero patient traffic from that specific
chart. `WHERE` couldn't do that second part at all.

### 6. Why might `COUNT(*)` and `COUNT(email)` give different answers on the same table?

**Tests:** `NULL` handling, a very common real bug source.

**Answer:** `COUNT(*)` counts rows regardless of their contents.
`COUNT(column)` counts only rows where that column is non-`NULL`. Our
`patients.email` column is nullable (not every patient provides one), so
`COUNT(email)` answers "how many patients have an email on file," while
`COUNT(*)` answers "how many patients exist" — using the wrong one would
silently misreport patients-without-email as patients-without-records.

### 7. How did you generate patient numbers without risking a collision under concurrent registrations?

**Tests:** whether you understand why `SELECT MAX(x)+1` is a real,
common concurrency bug.

**Answer:** I used a Postgres `SEQUENCE` (`patient_number_seq`) and pulled
the next value with `nextval()`, formatting it as `PT-000123`. A naive
`SELECT MAX(patient_number)` approach has a real race condition: two
concurrent registrations could both read the same current max before
either commits, and both compute the same "next" number. A `SEQUENCE`'s
`nextval()` is atomic at the database level — Postgres guarantees no two
callers ever get the same value, even under heavy concurrency, with no
row locking required on the `patients` table itself. Worth noting:
sequences are deliberately *not* transactional — if an insert using a
pulled value later fails and rolls back, that number is still "burned"
and never reused, which is why our patient numbers can have small gaps
(a real, expected behavior we observed directly during Module 4 testing).

---

## FastAPI

### 8. How does FastAPI's dependency injection let you swap the database in tests without touching route code?

**Tests:** real understanding of `Depends()` beyond "it injects stuff."

**Answer:** Every route that needs a database session declares
`db: Session = Depends(get_db)`, where `get_db` is a plain generator
function. FastAPI resolves this per-request, normally creating a fresh
session against the real database. In tests, `app.dependency_overrides[get_db] = override_get_db`
tells FastAPI to call a *different* callable instead — one that yields a
test-only session wrapped in a transaction that gets rolled back after
the test. No route or service code changes at all; the override is
purely at the app-instance level, cleared after each test.

### 9. Why did you write global exception handlers instead of handling errors in every route?

**Tests:** understanding of centralized cross-cutting concerns and how
Starlette actually dispatches exceptions.

**Answer:** With 60+ `raise HTTPException(...)` call sites across the
codebase by Module 11, rewriting each one to produce a consistent error
shape would have been both a huge, risky diff and something every future
route would need to remember to replicate. Instead, I registered handlers
for specific exception types (`StarletteHTTPException`,
`RequestValidationError`, `SQLAlchemyError`, and a generic `Exception`
catch-all) at the app level. Starlette dispatches a raised exception to
the *most specific* registered handler for its exact type, falling back
through the class hierarchy — so the generic `Exception` handler only
ever catches things nothing more specific matched, and every existing
`raise HTTPException(...)` call automatically gets reshaped into one
consistent `{"error": {"code", "message", "details"}}` envelope with zero
changes to the routes themselves.

### 10. What's the actual difference between a 401 and a 403 in your API, and where's that enforced?

**Tests:** authentication vs. authorization, a distinction people often
blur.

**Answer:** `401` means "I don't know who you are" — no token, an
expired token, or a token whose signature doesn't verify; that's handled
entirely inside the `get_current_user` dependency, before any route logic
runs. `403` means "I know exactly who you are, and you're not allowed to
do this" — enforced by `require_role(...)`, a dependency *factory* that
takes a list of allowed roles and returns a dependency checking the
already-authenticated user's role against it. I confirmed this
distinction directly in testing: a `PATIENT`-role token hitting a
doctor-only endpoint correctly returns `403`, not `401`, because the
token itself is completely valid — it's just not permitted there.

---

## PostgreSQL

### 11. Why a native Postgres `ENUM` for role/status columns instead of `VARCHAR` + `CHECK`?

**Tests:** awareness of the actual trade-off, not just "it's stricter."

**Answer:** A native `ENUM` is stricter — it's structurally impossible to
insert an invalid value, versus a `CHECK` constraint which is just
another rule the database happens to enforce. The real trade-off is
schema evolution: adding a new enum value later requires `ALTER TYPE ...
ADD VALUE`, a real (if usually fine) migration, whereas updating a
`CHECK` constraint's allowed list is a smaller change. I used native
`ENUM`s for things with a small, well-known, rarely-changing set of
values (user roles, appointment/lab/invoice statuses) where the extra
strictness is worth it, and plain strings for genuinely open-ended
fields like a doctor's `specialization`, where new values get added
constantly as real staff data.

### 12. Explain the partial unique index you used to prevent double-booking. Why not a plain unique constraint?

**Tests:** understanding of partial indexes and the actual business rule
behind them.

**Answer:**
```sql
CREATE UNIQUE INDEX ux_appointments_doctor_slot
  ON appointments (doctor_id, appointment_date, appointment_time)
  WHERE status != 'CANCELLED';
```
A plain unique constraint on `(doctor_id, appointment_date,
appointment_time)` would permanently block rebooking that exact slot even
after the original appointment was cancelled — which is wrong; a
cancelled appointment should free the slot. The `WHERE` clause makes the
uniqueness conditional: only *non-cancelled* appointments are considered
for the constraint. I verified this directly — cancelling an appointment
and immediately rebooking the identical doctor/date/time succeeded, while
attempting to double-book an active slot correctly failed with a
database-level conflict, not just an application-level check (which
would have a real race condition between the check and the insert).

### 13. What does `EXPLAIN ANALYZE` show you that `EXPLAIN` alone doesn't?

**Tests:** real hands-on experience, not textbook recall.

**Answer:** Plain `EXPLAIN` shows the planner's *estimated* plan and cost
— what Postgres *thinks* it'll do, based on table statistics. `EXPLAIN
ANALYZE` actually *runs* the query and reports real, measured numbers:
actual row counts and actual execution time per plan node. I used this
directly in Module 11: I bulk-loaded 200,000 synthetic `lab_orders` rows,
ran `EXPLAIN ANALYZE` on `SELECT * FROM lab_orders WHERE status =
'PENDING'` before adding an index (a `Seq Scan`, 27.294ms actual
execution time), added the index, ran `ANALYZE` to refresh planner
statistics, then ran the same `EXPLAIN ANALYZE` again — it switched to an
`Index Scan`, 4.412ms. Without the `ANALYZE` step specifically, the
planner can make a decision based on stale statistics even after the
index exists.

---

## Healthcare Integration

### 14. What's the actual difference between HL7v2 and FHIR, and why model FHIR resources instead of HL7v2 messages?

**Tests:** genuine domain knowledge, not buzzword recognition.

**Answer:** HL7v2 (still widely used in real hospitals) is a pipe-delimited
text message format from the 1980s — messages like `MSH|^~\&|...` for
things like lab results or ADT events. FHIR is HL7's modern standard:
REST/JSON-based, organizing data into typed, linked **resources**
(`Patient`, `Encounter`, `Observation`). I modeled FHIR specifically
because it maps much more naturally onto a JSON API (which is what our
whole backend already is), and because current interoperability
requirements (in the US, ONC/CMS rules) increasingly mandate FHIR APIs
for certified health IT — it's the direction the industry has moved.

### 15. Your FHIR `Patient` mapping sends `patient_number` to the simulated external system, not the patient's name. Why?

**Tests:** data-minimization awareness — do you think about what an
external system actually needs vs. what's convenient to send?

**Answer:** The `LimsOrderRequest`/`PaymentGatewayRequest`/FHIR export
request objects only carry what the receiving system needs to do its
job — an identifier and the relevant clinical/financial data — not
identifying PHI like a name unless the resource type genuinely requires
it (a FHIR `Patient` resource necessarily includes name, since that's
its whole purpose). For the LIMS integration specifically, I used
`patient_number` rather than the patient's name in the request sent
"externally," on the principle that you should never send more personal
data across a system boundary than is actually required for the
receiving system's function.

### 16. You didn't implement the full FHIR spec. What did you leave out, and how did you decide what was "enough"?

**Tests:** honest scoping judgment — can you draw a line and defend it,
rather than overclaiming?

**Answer:** I implemented three resource types (`Patient`, `Encounter`,
`Observation`) with only the fields needed to demonstrate a genuine,
correct mapping — structured names, coded administrative gender,
references between resources, a real `value[x]` choice (`valueQuantity`
for numeric lab results, `valueString` for qualitative ones like
"Positive"). I explicitly did not implement the full resource
definitions (extensions, the dozens of optional fields each real FHIR
resource supports), FHIR search parameters, or actual conformance to any
published Implementation Guide. The line I drew: enough to correctly
demonstrate the *mapping problem* (internal shape → external standard
shape, including real gotchas like a field named `class` colliding with
a Python reserved word) without claiming certified interoperability,
which this project has been explicit about not being.

---

## Debugging

### 17. You mentioned finding a bug where a re-queried object returned stale data within the same request. What happened?

**Tests:** real, specific ORM understanding — not something you can fake
without having actually hit it.

**Answer:** In `encounter_service.add_clinical_record`, I called
`get_encounter()` before inserting a new `ClinicalRecord`, then called it
*again* after committing, expecting the fresh record to appear in the
returned `clinical_records` list. It came back empty both times. The
cause: SQLAlchemy's session-level identity map returned the *same Python
object* for the second call (matched by primary key), and since that
object's `clinical_records` collection was already loaded (as empty,
from the first call) and not expired, a second `selectinload` against an
already-populated collection is a no-op by default — it doesn't silently
know to re-fetch just because new rows exist. The fix was adding
`.execution_options(populate_existing=True)` to force a genuine re-fetch
of already-mapped objects, which I then also applied proactively to the
analogous lab-order code in Module 7 once I knew the pattern.

### 18. A custom Pydantic validator raising `ValueError` broke your global error handler. What was actually happening?

**Tests:** a real, specific bug from Module 11 — tests whether you
understand the fix, not just that it happened.

**Answer:** Our `Patient.date_of_birth` field has a custom
`@field_validator` that raises `ValueError` if the date is in the future.
When that validation fails, Pydantic's `RequestValidationError.errors()`
embeds the *actual exception object* inside the error's `ctx.error`
field, not a string. My global validation handler was constructing a
`JSONResponse` directly from that error list, and Starlette's
`JSONResponse` uses plain `json.dumps` internally, which can't serialize
an arbitrary Python exception object — every request that hit this
specific validator crashed with a 500 instead of returning the intended
422. FastAPI's own *default* handler avoids this by running the error
list through `fastapi.encoders.jsonable_encoder` first, which knows how
to convert Pydantic-specific error structures into JSON-safe primitives.
My custom handler needed to do the same thing explicitly — a one-line
fix once identified, but a real gap a self-written handler can introduce
silently if you don't test the exact path that triggers it (which is
exactly how I found it — an actual failing test, not a code review).

---

## Deployment

### 19. Your local dev database and production database ended up pointed at the same place at one point. What happened, and how did you avoid real damage?

**Tests:** environment discipline, and honesty about a real operational
near-miss rather than pretending everything went smoothly.

**Answer:** During the initial deployment work, `backend/.env`'s
`DATABASE_URL` was updated to point at the live Neon production database
so I could verify the deployed app worked — but that same `.env` file is
also what local development reads. In a later module, before creating any
test data, I checked the actual state of the target database first and
noticed it only contained the one production admin account, not the
various test doctors/patients that should have existed locally — which
is what revealed the mismatch. Because I checked before writing anything,
no test data ever polluted production; I then pointed `.env` back at the
local Postgres instance and re-ran the pending migration against it to
bring it back in sync. The general practice this reinforced: always
verify which environment you're actually pointed at before running
anything that writes data, especially after any step that intentionally
changes connection configuration.

### 20. Why does your Dockerized frontend need the backend's URL at *build* time, while the backend reads its configuration at container *startup*?

**Tests:** understanding of a real, concrete difference between a static
frontend bundle and a running server process.

**Answer:** Our backend uses Pydantic `Settings`, which reads environment
variables fresh every time the process starts — so the same Docker image
can run in different environments just by changing the injected env
vars, no rebuild needed. Vite works completely differently: `import.meta.env.VITE_API_URL`
references get replaced with literal string values *at build time*, when
`npm run build` compiles the React app into static JS/CSS/HTML files.
Once that build finishes, the value is frozen into those static files —
there's no running process left to read a new environment variable from.
This is why the frontend `Dockerfile` takes `VITE_API_URL` as a build
`ARG`, not a runtime `ENV`: changing it after the image is built requires
rebuilding the image, not just restarting the container, which is a real
and easy-to-miss difference between how frontend and backend
configuration actually work.
