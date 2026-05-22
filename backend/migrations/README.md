Migration notes
----------------

Files added:
- `001_add_display_fields.sql` : direct SQL migration for display + AI config fields + patrol ROI
- `002_add_display_fields_alembic.py` : alembic-style helper for projects using Alembic

How to apply (Postgres):

- SQL (psql):
  psql "$DATABASE_URL" -f backend/migrations/001_add_display_fields.sql

- Alembic: place `002_add_display_fields_alembic.py` into your Alembic `versions/` folder and run:
  alembic upgrade head

Notes:
- Ensure you have a DB backup before applying migrations.
- If your project doesn't use Alembic, use the SQL file.
- The camera schema now includes `patrol_region_json` for periodic patrol monitoring.
Migration instructions

1) Ensure `DATABASE_URL` environment variable is set and points to your backend Postgres, for example:

   setx DATABASE_URL "postgresql://postgres:password@localhost:5432/camera_db"

2) From the `backend/migrations` folder run:

   psql "%DATABASE_URL%" -f 001_add_display_fields.sql

On Linux/macOS use:

   psql "$DATABASE_URL" -f 001_add_display_fields.sql

If you use Alembic, convert this SQL into an Alembic revision or run it via your migration tooling.
