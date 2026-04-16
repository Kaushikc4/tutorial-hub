# 📚 Tutorial Hub

A full-stack tutorial center platform for teachers and students. Teachers upload notes, worksheets, and question papers; students submit their answers; everyone gets a clean dashboard to track it all.

**Stack:** Django REST API · Streamlit UI · PostgreSQL · Docker · AWS S3

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🗂️ Project Structure](#️-project-structure)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Environment Variables](#️-environment-variables)
- [🗄️ Data Models](#️-data-models)
- [🐳 Docker Services](#-docker-services)
- [☁️ Deploying to AWS](#️-deploying-to-aws)
- [🔮 Planned Features](#-planned-features)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

**For Teachers**
- Upload notes, worksheets, and question papers (PDF, Word, images)
- Set due dates and total marks per assignment
- Review all student submissions in one place
- Grade submissions with marks and written feedback
- View individual student profiles and progress

**For Students**
- Personal dashboard with enrolled subjects and pending tasks
- Download materials and upload completed answers
- Track submission status — pending, graded, or returned
- View scores and teacher feedback per submission

**Analytics (Streamlit)**
- Submission trends over time
- Score distribution and top performers
- Material breakdown by type and subject
- Enrollment stats per subject

---

## 🗂️ Project Structure

```
tutorial-hub/
├── tutorials_backend/     # Django REST API
│   ├── core/              # Models, views, serializers
│   ├── manage.py
│   └── requirements.txt
├── tutorials_frontend/    # Streamlit UI
│   ├── app.py
│   └── requirements.txt
├── docker-compose.yml
├── DEPLOY_AWS.md
└── .gitignore
```

---

## 🚀 Quick Start

### With Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/Kaushikc4/tutorial-hub.git
cd tutorial-hub

# 2. Start all services
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Django API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |
| Streamlit UI | http://localhost:8501 |
| PostgreSQL | localhost:5432 |

### Without Docker

**Backend**
```bash
cd tutorials_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up your PostgreSQL database, then:
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Frontend**
```bash
cd tutorials_frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root (Docker will pick it up automatically):

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
PGHOST=postgres
PGPORT=5432
PGDATABASE=tutorials
PGUSER=postgres
PGPASSWORD=postgres

# AWS S3 (optional — for file storage in production)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1

# Streamlit
TUTORIAL_API_URL=http://localhost:8000/api/tutorial
```

> If AWS variables are left empty, files are stored locally. See [DEPLOY_AWS.md](./DEPLOY_AWS.md) for S3 setup.

---

## 🗄️ Data Models

| Model | Description |
|-------|-------------|
| `User` | Extended Django user with `teacher` / `student` role |
| `Subject` | A course or topic (e.g. Mathematics, English) |
| `Enrollment` | Links a student to a subject with their assigned teacher |
| `Material` | Uploaded file — type: `note`, `worksheet`, or `question_paper` |
| `StudentSubmission` | A student's uploaded answer file, with grading fields |
| `Announcement` | Pinnable notices from teachers, global or per-subject |
| `Notification` | In-app alerts for new uploads, grades, and submissions |

---

## 🐳 Docker Services

```yaml
postgres   # PostgreSQL 16 — primary database
backend    # Django REST API — port 8000
frontend   # Streamlit UI — port 8501
```

The backend waits for PostgreSQL to be healthy before starting (via `healthcheck`).

---

## ☁️ Deploying to AWS

See [DEPLOY_AWS.md](./DEPLOY_AWS.md) for a step-by-step guide covering:
- EC2 setup and SSH access
- RDS PostgreSQL provisioning
- S3 bucket configuration for file uploads
- Environment variable management
- Running with Docker on the server

---

## 🔮 Planned Features

- [ ] JWT authentication with refresh tokens
- [ ] REST API documentation (Swagger / drf-spectacular)
- [ ] Email notifications via SES or SendGrid
- [ ] AI-assisted feedback on submissions
- [ ] Parent portal (read-only progress view)
- [ ] Mobile-friendly frontend

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push and open a pull request

---

## 📄 License

MIT — feel free to use, modify, and distribute.
