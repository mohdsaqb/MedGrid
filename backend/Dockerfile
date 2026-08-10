# Matches the Python version pinned in runtime.txt for the Render deploy -
# keeping dev, CI, and every deployment target on the same interpreter
# version is exactly the "works identically everywhere" promise of
# containers (Part 1, point 1).
FROM python:3.12-slim

WORKDIR /app

# Dependencies copied and installed BEFORE the rest of the app code, on
# purpose: Docker caches each instruction as a layer, and only re-runs a
# layer if its inputs changed. Since requirements.txt changes far less
# often than application code, this ordering means `pip install` is
# skipped entirely on most rebuilds - only touching a .py file won't
# invalidate this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Migrations run before the server starts - same pattern used for the
# Render deployment in the earlier deployment work.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
