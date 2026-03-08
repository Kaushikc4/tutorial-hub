# Deploy Tutorial Hub on AWS (EC2, S3, PostgreSQL)

You're logged in as the **root** account. Use root only for one-time setup (e.g. creating an IAM user). For day-to-day and automation, use an **IAM user** with limited permissions. That way you avoid accidental billing/security impact and follow AWS best practices.

---

## 1. Create an IAM user (do this as root, then stop using root)

1. In the AWS Console go to **IAM → Users → Create user**.
2. User name: e.g. `tutorial-hub-deploy`.
3. **Access type**:  
   - **Programmatic access** (for CLI, GitHub Actions, EC2 if you use keys).  
   - Optionally **Console access** if you want to log in as this user in the browser.
4. **Permissions**: attach policies. Prefer **least privilege** instead of "superuser":
   - **Option A (recommended)**  
     - `AmazonEC2FullAccess`  
     - `AmazonS3FullAccess`  
     - (If you later use RDS: `AmazonRDSFullAccess`.)  
     This is enough to run EC2, create S3 buckets, and store files. No IAM or billing changes.
   - **Option B (broad)**  
     - `AdministratorAccess`  
     Use only if you intentionally want this user to do everything. Avoid for routine use.
5. Complete user creation. **Save the Access Key ID and Secret Access Key** (you won't see the secret again). Use these for:
   - AWS CLI on your machine or on EC2  
   - Env vars `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for the app (S3).

From here on, use this IAM user (or its keys) for deploying and running the app, not root.

---

## 2. S3 bucket for uploaded files

1. **S3 → Create bucket** (e.g. `tutorial-hub-uploads-<account-id>`).
2. Region: same as your EC2 (e.g. `us-east-1`).
3. Block public access: **keep all on** (app will use IAM credentials to read/write).
4. Create the bucket.
5. Note the **bucket name** and **region** for env vars:
   - `AWS_STORAGE_BUCKET_NAME`
   - `AWS_S3_REGION_NAME`

The Django app uses **django-storages** and **boto3**; when these env vars (and the IAM user's keys) are set, uploads go to S3 instead of local disk.

---

## 3. EC2 instance (app + PostgreSQL on the same host)

1. **EC2 → Launch instance**  
   - Name: e.g. `tutorial-hub`.  
   - AMI: **Amazon Linux 2023** or **Ubuntu 22.04**.  
   - Instance type: e.g. `t2.small` (or `t2.micro` for testing).  
   - Key pair: create or select one; you need the `.pem` to SSH.  
   - Storage: default is fine.

2. **Security group** (create or edit):  
   - **22** (SSH) from your IP.  
   - **80** (HTTP) from `0.0.0.0/0` if you want direct HTTP (or restrict to your IP/ALB).  
   - **8000** (Django) and **8501** (Streamlit) from `0.0.0.0/0` if you're not using a reverse proxy yet (you can tighten later with nginx/ALB).

3. Launch, then **connect** via SSH (e.g. "EC2 Instance Connect" or `ssh -i your.pem ec2-user@<public-ip>`).

4. **On the EC2 instance** (Amazon Linux example; Ubuntu use `apt` and `ubuntu` user):

   ```bash
   sudo yum update -y
   sudo yum install -y docker
   sudo systemctl start docker && sudo systemctl enable docker
   sudo usermod -aG docker ec2-user
   ```

   Install Docker Compose (v2):

   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

   Log out and back in so `docker` group applies, or run the next steps with `sudo`.

5. **Clone your repo** (or copy the project onto the instance):

   ```bash
   git clone https://github.com/<you>/tutorial-hub.git
   cd tutorial-hub
   ```

6. **Environment variables**  
   Create a `.env` in the project root (or export in the same shell where you run Compose). Use the IAM user's keys and the S3 bucket:

   ```bash
   export DJANGO_SECRET_KEY="your-strong-secret-key"
   export DJANGO_ALLOWED_HOSTS="*"
   export AWS_ACCESS_KEY_ID="AKIA..."
   export AWS_SECRET_ACCESS_KEY="..."
   export AWS_STORAGE_BUCKET_NAME="tutorial-hub-uploads-..."
   export AWS_S3_REGION_NAME="us-east-1"
   ```

   For **PostgreSQL** (already in `docker-compose`), the backend uses the same Postgres service; set a strong password if you open the DB to the internet (not recommended), or leave as in `docker-compose` for local-to-EC2 only:

   ```bash
   export PGPASSWORD="postgres"   # or a strong password; match docker-compose
   ```

   Pass these into the backend container (e.g. in `docker-compose.yml` under `backend.environment` with `${VAR}` and run `docker compose` in the same env, or use an env file).

7. **Run the stack** (Postgres + backend + frontend on the same EC2):

   ```bash
   docker compose up -d
   ```

   Run migrations (one-off, or let entrypoint run them):

   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py createsuperuser  # optional
   ```

8. **Open the app**  
   - API: `http://<ec2-public-ip>:8000/api/tutorial/`  
   - UI: `http://<ec2-public-ip>:8501`

PostgreSQL runs in the same `docker-compose` on this EC2; no separate RDS needed unless you want managed DB later.

---

## 4. Summary

| Item | What to do |
|------|------------|
| **Root** | Use only to create the IAM user; then use that user (or its keys) for everything else. |
| **IAM user** | Create one (e.g. `tutorial-hub-deploy`) with EC2 + S3 (and RDS if needed). Attach policies; avoid broad "superuser" unless required. |
| **Containers** | Backend (Django + Gunicorn) and frontend (Streamlit) in Docker; `docker-compose` also runs Postgres on the same EC2. |
| **Files** | Stored in S3 when `AWS_STORAGE_BUCKET_NAME` and IAM keys are set; otherwise local to the backend container. |
| **Postgres** | Runs in EC2 via `docker-compose` (postgres service). |

For production you'll want HTTPS (e.g. nginx + Let's Encrypt or an ALB), restrict security groups, and keep `DJANGO_SECRET_KEY` and DB passwords in a secrets manager; this guide gets you running with the container on EC2, S3 for files, and Postgres on the same instance.
