# PostgreSQL table names and example queries

In PostgreSQL, table names are **lowercase**. Django creates these tables.

**Warning:** In SQL, `user` is a built-in (current DB user). The profile table has **`user_id`**, not `user`. Use `user_id` and join to `auth_user` for the login name.

## Table names (use these in `psql`)

| Django model     | Actual table name                      |
|------------------|----------------------------------------|
| User (auth)      | `auth_user`                            |
| Profile          | `tutorial_profile`                     |
| TeacherStudent   | `tutorial_teacher_student`             |
| Material         | `tutorial_material`                    |
| Material ↔ students (M2M) | `tutorial_material_target_students` |
| StudentSubmission | `tutorial_student_submission`         |
| Auth token       | `authtoken_token`                      |

## List all tables

```sql
\dt
```

## Example queries

```sql
-- Users (Django auth) — username is here
SELECT id, username, is_staff FROM auth_user;

-- Profiles: use user_id (FK to auth_user), not "user"
SELECT id, role, full_name, user_id FROM tutorial_profile;

-- Profiles with login username (join)
SELECT p.id, p.role, p.full_name, u.username
FROM tutorial_profile p
JOIN auth_user u ON u.id = p.user_id;

-- Teacher–student assignments
SELECT * FROM tutorial_teacher_student;

-- Materials
SELECT id, title, material_type, uploaded_by_id, created_at FROM tutorial_material;

-- Count rows
SELECT 'auth_user' AS tbl, COUNT(*) FROM auth_user
UNION ALL SELECT 'tutorial_profile', COUNT(*) FROM tutorial_profile
UNION ALL SELECT 'tutorial_material', COUNT(*) FROM tutorial_material;
```

## Describe a table (columns)

```sql
\d auth_user
\d tutorial_profile
\d tutorial_material
```
