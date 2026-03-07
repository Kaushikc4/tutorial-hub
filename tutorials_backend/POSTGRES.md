# Using PostgreSQL with the tutorials backend

## 0. Use Postgres every time (so the project doesn’t fall back to SQLite)

Set **PGDATABASE** (and other Postgres env vars) in the **same terminal** where you run `manage.py runserver`. Django uses Postgres when `PGDATABASE` or `DJANGO_DB_ENGINE=postgresql` is set.

**Option A – this terminal only:**

```bash
cd tutorials_backend
export PGDATABASE=tutorials
export PGUSER=tutorials_user
export PGPASSWORD=your_password
export PGHOST=localhost
export PGPORT=5432
python manage.py runserver
```

**Option B – every new terminal (add to `~/.bashrc` or `~/.profile`):**

```bash
# Tutorials backend – use PostgreSQL
export PGDATABASE=tutorials
export PGUSER=tutorials_user
export PGPASSWORD=your_password
export PGHOST=localhost
export PGPORT=5432
```

Then open a new terminal, `cd tutorials_backend`, and run `python manage.py runserver`; it will use Postgres.

**Option C – run script:** use `./run_with_postgres.sh` (see script in this folder; set the password inside it once).

---

## 1. Switch Django to PostgreSQL (first-time setup)

Create a database and user (from your OS user or postgres superuser):

```bash
# In psql as superuser (e.g. postgres):
CREATE DATABASE tutorials;
CREATE USER tutorials_user WITH PASSWORD 'your_password';
ALTER ROLE tutorials_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE tutorials TO tutorials_user;
\q
```

Set environment variables and run migrations:

```bash
cd tutorials_backend

export DJANGO_DB_ENGINE=postgresql
export PGDATABASE=tutorials
export PGUSER=tutorials_user
export PGPASSWORD=your_password
export PGHOST=localhost
export PGPORT=5432

pip install -r requirements.txt
python manage.py migrate
```

(On Windows use `set VAR=value` instead of `export`.)

## 2. Inspect tables with PostgreSQL

Connect with the `psql` client:

```bash
psql -h localhost -p 5432 -U tutorials_user -d tutorials
# or: psql "postgresql://tutorials_user:your_password@localhost:5432/tutorials"
```

### List all tables

```sql
\dt
```

### Tutorial app tables (and related)

| Table | Description |
|-------|-------------|
| `tutorial_profile` | Students and teachers (links to auth_user) |
| `tutorial_teacher_student` | Teacher–student assignments |
| `tutorial_material` | Notes, worksheets, question papers |
| `tutorial_material_target_students` | M2M: which students a material is for |
| `tutorial_student_submission` | Student answer uploads |
| `auth_user` | Django users |
| `authtoken_token` | API tokens |

### Describe a table (columns and types)

```sql
\d tutorial_profile
\d tutorial_material
\d tutorial_teacher_student
```

### Example queries

```sql
-- Count profiles by role
SELECT role, COUNT(*) FROM tutorial_profile GROUP BY role;

-- List teachers and their assigned student count
SELECT p.id, p.full_name, COUNT(ts.student_id) AS students
FROM tutorial_profile p
LEFT JOIN tutorial_teacher_student ts ON ts.teacher_id = p.id
WHERE p.role = 'teacher'
GROUP BY p.id, p.full_name;

-- List materials with uploader name
SELECT m.id, m.title, m.material_type, p.full_name AS uploaded_by
FROM tutorial_material m
LEFT JOIN tutorial_profile p ON m.uploaded_by_id = p.id
ORDER BY m.created_at DESC;
```

### Quit psql

```sql
\q
```

## 3. Optional: use SQLite again

Unset the Postgres env vars (or don’t set them) and run with SQLite:

```bash
unset DJANGO_DB_ENGINE PGDATABASE PGUSER PGPASSWORD PGHOST PGPORT
python manage.py runserver
```
