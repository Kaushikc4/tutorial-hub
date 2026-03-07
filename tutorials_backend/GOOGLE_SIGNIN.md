# Google Sign-In setup

The app supports **Sign in with Google** and **Sign up with Google** in addition to email/username + password.

---

## Quick setup (3 steps)

### 1. Get Google OAuth credentials (free, ~2 minutes)

1. Open **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Create a project (or pick an existing one).
3. Go to **APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**.
4. If prompted, set up the **OAuth consent screen**: choose **External**, add your email as a test user.
5. Application type: **Web application**.
6. Under **Authorized redirect URIs** click **Add URI** and add exactly:
   ```text
   http://localhost:8000/api/tutorial/auth/google/callback/
   ```
   (Use your real Django URL if you’re not on localhost.)
7. Create the client and copy the **Client ID** and **Client secret**.

### 2. Put them in a `.env` file

From the `tutorials_backend` folder:

```bash
cp .env.example .env
```

Edit `.env` and paste your Client ID and Client secret:

```text
GOOGLE_OAUTH_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
TUTORIAL_FRONTEND_URL=http://localhost:8501
```

Save the file. Django loads `.env` automatically when the server starts.

### 3. Restart the Django server

Stop the server (Ctrl+C) and start it again so it reads `.env`. Then try **Sign in with Google** again.

---

## Optional: use environment variables instead of `.env`

You can also set the values in the shell before running the server:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
export TUTORIAL_FRONTEND_URL="http://localhost:8501"
python manage.py runserver
```

---

## Details

- **GOOGLE_OAUTH_CLIENT_ID** – Required for the Google button to work; backend returns 503 if missing.
- **GOOGLE_OAUTH_CLIENT_SECRET** – Required for the callback to exchange the code for a token.
- **TUTORIAL_FRONTEND_URL** – Where to send the user after Google login (your Streamlit app). Defaults to `http://localhost:8501` if unset.

## 3. Flow

1. User clicks **Sign in with Google** (or **Sign up with Google**) in the Streamlit app.
2. They are sent to Google to sign in.
3. Google redirects to your Django callback URL with a `code`.
4. Django exchanges the code for tokens, gets the user’s email/name, creates or finds the User and Profile, creates an API token, and redirects to `TUTORIAL_FRONTEND_URL?token=...`.
5. Streamlit reads the token from the URL, stores it in session, and the user is logged in.

New users signing in with Google get a **Student** profile by default; you can change this in `tutorials/views.py` in `_google_callback_view` if you want a different default.
