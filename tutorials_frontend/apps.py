"""
    Tutorial Center — Enterprise-style Streamlit UI
"""
import html
import os
import requests
import streamlit as st

# Default API base; override with env TUTORIAL_API_URL
API_BASE = os.environ.get("TUTORIAL_API_URL", "http://localhost:8000/api/tutorial")

# ─── Dark theme & layout ───────────────────────────────────────────────────
APP_CSS = """
<style>
    /* Dark app background */
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #020617 100%); }
    [data-testid="stHeader"] { background: rgba(15, 23, 42, 0.95); border-bottom: 1px solid #334155; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] { color: #94a3b8; }

    /* Expanders and blocks blend with dark background */
    [data-testid="stExpander"] { border: 1px solid #334155; border-radius: 8px; }

    /* Brand block (auth page) */
    .brand-block {
        text-align: center; padding: 2rem 1rem 1.5rem;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f1f5f9; border-radius: 12px 12px 0 0;
        margin-bottom: 0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3);
        border: 1px solid #334155; border-bottom: none;
    }
    .brand-block h1 { font-size: 1.75rem; font-weight: 600; margin: 0; letter-spacing: -0.02em; color: #fff; }
    .brand-block p { margin: 0.25rem 0 0; opacity: 0.9; font-size: 0.95rem; color: #94a3b8; }

    /* Content cards in main area (dark) */
    .content-card {
        background: #1e293b; border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.2); border: 1px solid #334155;
    }
    .section-title { font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 0.75rem; }

    /* Sidebar nav buttons */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100%; justify-content: flex-start; text-align: left;
        background: transparent; color: #e2e8f0; border: none;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.1); color: #fff;
    }

    /* Headings dark mode */
    h1, h2, h3 { font-weight: 600; color: #f1f5f9 !important; }
    .stSubheader { color: #f1f5f9 !important; }

    /* Tighter default spacing */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }
</style>
"""


def inject_app_css():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def api_headers():
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Token {token}"}


def get(path, **kwargs):
    return requests.get(f"{API_BASE}{path}", headers=api_headers(), **kwargs)


def post(path, **kwargs):
    return requests.post(f"{API_BASE}{path}", headers=api_headers(), **kwargs)


def put(path, **kwargs):
    return requests.put(f"{API_BASE}{path}", headers=api_headers(), **kwargs)


def delete(path, **kwargs):
    return requests.delete(f"{API_BASE}{path}", headers=api_headers(), **kwargs)


def ensure_token():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "section" not in st.session_state:
        st.session_state.section = None  # student: notes, worksheets, test_papers, my_submissions; teacher: my_students, my_personal_notes
    if "teacher_selected_student_id" not in st.session_state:
        st.session_state.teacher_selected_student_id = None
    if "teacher_student_section" not in st.session_state:
        st.session_state.teacher_student_section = None
    # if "pending_google_redirect" not in st.session_state:
    #     st.session_state.pending_google_redirect = None

# def _google_auth_url():
#     """Return Google OAuth URL from backend, or None if not configured."""
#     try:
#         r = requests.get(f"{API_BASE}/auth/google/", timeout=5)
#         if r.status_code == 200:
#             return r.json().get("url")
#     except Exception:
#         pass
#     return None


def login_form():
    st.subheader("Sign in")
    # Google Sign-In (commented out for now)
    # google_url = _google_auth_url()
    # if st.button("Sign in with Google", type="primary", use_container_width=True, key="btn_google_login"):
    #     if google_url:
    #         st.session_state.pending_google_redirect = google_url
    #         st.rerun()
    #     else:
    #         st.error(
    #             "Google Sign-In is not configured. On the server, set GOOGLE_OAUTH_CLIENT_ID and "
    #             "GOOGLE_OAUTH_CLIENT_SECRET (see tutorials_backend/GOOGLE_SIGNIN.md)."
    #         )
    # st.caption("— or sign in with email/username —")
    with st.form("login"):
        username = st.text_input("Email or username", placeholder="Enter your email or username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.form_submit_button("Log in"):
            r = post("/login/", data={"username": username, "password": password})
            if r.status_code == 200:
                data = r.json()
                st.session_state.token = data["token"]
                r2 = get("/profile/me/")
                if r2.status_code == 200:
                    st.session_state.profile = r2.json()
                # Persist token in URL so reload keeps you logged in
                try:
                    st.query_params["token"] = data["token"]
                except Exception:
                    pass
                st.rerun()
            else:
                try:
                    err = r.json()
                    msg = err.get("detail", err) if isinstance(err, dict) else str(err)
                except Exception:
                    msg = r.text or f"Login failed (HTTP {r.status_code})"
                st.error(msg)


def register_form():
    st.subheader("Create account")
    # Google Sign-up (commented out for now)
    # google_url = _google_auth_url()
    # if st.button("Sign up with Google", type="primary", use_container_width=True, key="btn_google_register"):
    #     if google_url:
    #         st.session_state.pending_google_redirect = google_url
    #         st.rerun()
    #     else:
    #         st.error(
    #             "Google Sign-In is not configured. On the server, set GOOGLE_OAUTH_CLIENT_ID and "
    #             "GOOGLE_OAUTH_CLIENT_SECRET (see tutorials_backend/GOOGLE_SIGNIN.md)."
    #         )
    # st.caption("— or register with email/username —")
    with st.form("register"):
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email (optional)", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        full_name = st.text_input("Full name (optional)", placeholder="Your full name")
        role = st.selectbox("I am a", ["Student", "Teacher"])
        if st.form_submit_button("Register"):
            r = post("/register/", json={
                "username": username,
                "email": email or "",
                "password": password,
                "full_name": full_name or "",
                "role": role,
            })
            if r.status_code == 201:
                data = r.json()
                st.session_state.token = data["token"]
                st.session_state.profile = data["profile"]
                # Persist token in URL so reload keeps you logged in
                try:
                    st.query_params["token"] = data["token"]
                except Exception:
                    pass
                st.rerun()
            else:
                err = r.json().get("detail", r.text)
                st.error(err if isinstance(err, str) else str(err))


def logout():
    st.session_state.token = None
    st.session_state.profile = None
    try:
        # Remove token from URL so reload doesn't log back in
        if "token" in st.query_params:
            del st.query_params["token"]
    except Exception:
        pass
    st.rerun()


def section_notes(materials):
    notes = [m for m in materials if m["material_type"] == "note"]
    if not notes:
        st.info("No notes yet.")
        return
    st.subheader("Notes")
    for m in notes:
        with st.container():
            st.markdown(f"**{m['title']}**")
            if m.get("description"):
                st.caption(m["description"])
            if m.get("file_url"):
                st.markdown(f"[Download]({m['file_url']})")
            st.divider()


def _render_material_view_only(material, label):
    """Show material (title, description, download) only — no submit option."""
    with st.container():
        st.markdown(f"**{material['title']}**")
        if material.get("description"):
            st.caption(material["description"])
        if material.get("file_url"):
            st.markdown(f"[Download {label}]({material['file_url']})")
        st.divider()


def section_worksheets(materials):
    worksheets = [m for m in materials if m["material_type"] == "worksheet"]
    if not worksheets:
        st.info("No worksheets yet.")
        return
    st.subheader("Worksheets")
    for m in worksheets:
        _render_material_view_only(m, "worksheet")


def section_test_papers(materials):
    question_papers = [m for m in materials if m["material_type"] == "question_paper"]
    if not question_papers:
        st.info("No test papers yet.")
        return
    st.subheader("Test Papers")
    for m in question_papers:
        _render_material_view_only(m, "question paper")


def section_my_submissions_student():
    r = get("/submissions/me/")
    if r.status_code != 200:
        st.error("Could not load submissions.")
        return
    subs = r.json()

    st.subheader("My Submissions")
    if not subs:
        st.info("You haven't submitted any answers yet.")
    else:
        for s in subs:
            with st.container():
                st.markdown(f"**{s.get('material_title')}** ({s.get('material_type', '').replace('_', ' ')})")
                st.caption(f"Submitted: {s.get('submitted_at', '')}")
                if s.get("answer_file_url"):
                    st.markdown(f"[Download my answer]({s['answer_file_url']})")
                if s.get("note"):
                    st.caption(s["note"])
                st.divider()

    # Submit option only on this page: pick a material and upload answer
    st.markdown("---")
    st.subheader("Submit an answer")
    r_mat = get("/materials/")
    materials = r_mat.json() if r_mat.status_code == 200 else []
    submitable = [m for m in materials if m.get("accepts_submissions")]
    submitted_ids = {s.get("material") for s in subs}
    available = [m for m in submitable if m["id"] not in submitted_ids]

    if not available:
        st.caption("No worksheets or test papers left to submit, or you’ve already submitted for all.")
        return

    with st.form("submit_answer_my_submissions"):
        material_options = {f"{m['title']} ({m['material_type'].replace('_', ' ')})": m for m in available}
        chosen_label = st.selectbox("Choose material", options=list(material_options.keys()))
        note = st.text_input("Note (optional)")
        file = st.file_uploader("Your answer file")
        if st.form_submit_button("Submit"):
            if not file:
                st.warning("Please select a file.")
            else:
                m = material_options[chosen_label]
                files = {"answer_file": (file.name, file.getvalue())}
                data = {"material": m["id"], "note": note or ""}
                r = post("/submissions/me/", data=data, files=files)
                if r.status_code == 201:
                    st.success("Submitted.")
                    st.rerun()
                else:
                    err = r.json() if getattr(r, "json", None) else {}
                    st.error(err.get("detail", r.text))


def get_display_name(profile):
    """Prefer display_name, then full_name, then username. Used in sidebar and greetings."""
    return (
        (profile.get("display_name") or "").strip()
        or profile.get("full_name")
        or profile.get("user", {}).get("username")
        or "there"
    )


def render_profile_header(profile, is_teacher=False):
    """Greeting and edit-profile form when that section is active. Nav is in sidebar."""
    if st.session_state.section == "edit_profile":
        st.subheader("Edit profile")
        with st.form("edit_profile"):
            full_name = st.text_input("Full name", value=profile.get("full_name") or "")
            display_name = st.text_input("Display name", value=profile.get("display_name") or "")
            if st.form_submit_button("Save"):
                r = put("/profile/me/", json={"full_name": full_name, "display_name": display_name})
                if r.status_code == 200:
                    st.session_state.profile = r.json()
                    st.success("Profile updated.")
                    st.session_state.section = None
                    st.rerun()
                else:
                    st.error("Could not update profile.")
        return
    # Small greeting line when not editing
    st.caption(f"Welcome back, **{get_display_name(profile)}**")


def student_home():
    profile = st.session_state.profile
    section = st.session_state.section

    if section == "edit_profile":
        render_profile_header(profile, is_teacher=False)
        return
    render_profile_header(profile, is_teacher=False)

    r = get("/materials/")
    materials = r.json() if r.status_code == 200 else []
    section = st.session_state.section

    if section == "notes":
        st.subheader("Notes")
        section_notes(materials)
    elif section == "worksheets":
        st.subheader("Worksheets")
        section_worksheets(materials)
    elif section == "test_papers":
        st.subheader("Test Papers")
        section_test_papers(materials)
    elif section == "my_submissions":
        st.subheader("My Submissions")
        section_my_submissions_student()
    else:
        st.subheader("Dashboard")
        st.markdown("Choose **Notes**, **Worksheets**, **Test Papers**, or **My Submissions** from the sidebar.")
        if not materials:
            st.info("No materials yet. Your teacher will add notes, worksheets, and test papers.")
        else:
            st.success(f"You have access to {len(materials)} material(s). Use the sidebar to open each section.")


def _student_display_name(p):
    return p.get("full_name") or p.get("user", {}).get("username") or f"Student {p.get('id')}"


def _materials_for_student(materials, student_id):
    """Filter materials to those visible to this student (no target_students or student in target_students)."""
    out = []
    for m in materials:
        targets = m.get("target_students") or []
        if not targets or any(t == student_id for t in targets):
            out.append(m)
    return out


def section_my_students_teacher(materials):
    """Show assigned students; each expander has 4 buttons (Notes, Worksheets, Test Papers, Submissions)."""
    r = get("/profiles/me/students/")
    if r.status_code != 200:
        st.error("Could not load your assigned students.")
        return
    students = r.json()
    if not students:
        st.info("No students assigned yet. Use **Assign student** below to add students.")
        _section_assign_students()
        return

    selected_id = st.session_state.teacher_selected_student_id
    sub_sec = st.session_state.teacher_student_section

    # If we have a selected student + section, show that content at the top
    if selected_id and sub_sec:
        student = next((s for s in students if s["id"] == selected_id), None)
        if student:
            st.markdown(f"**Viewing: {_student_display_name(student)}** — *{sub_sec.replace('_', ' ').title()}*")
            if st.button("← Back to student list", key="back_student_list"):
                st.session_state.teacher_selected_student_id = None
                st.session_state.teacher_student_section = None
                st.rerun()
            st.divider()
            filtered = _materials_for_student(materials, selected_id)
            if sub_sec == "notes":
                section_notes(filtered)
            elif sub_sec == "worksheets":
                section_worksheets(filtered)
            elif sub_sec == "test_papers":
                section_test_papers(filtered)
            elif sub_sec == "submissions":
                _render_student_submissions_for_teacher(selected_id)
            # Upload form defaulting to this student
            st.subheader(f"Upload for {_student_display_name(student)}")
            _upload_material_form(default_target_student_ids=[selected_id])
            return

    # List of students as expanders; inside each, 4 buttons
    st.subheader("My Students")
    for s in students:
        name = _student_display_name(s)
        with st.expander(f"**{name}**"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("📝 Notes", key=f"t_notes_{s['id']}", use_container_width=True):
                    st.session_state.teacher_selected_student_id = s["id"]
                    st.session_state.teacher_student_section = "notes"
                    st.rerun()
            with c2:
                if st.button("📄 Worksheets", key=f"t_ws_{s['id']}", use_container_width=True):
                    st.session_state.teacher_selected_student_id = s["id"]
                    st.session_state.teacher_student_section = "worksheets"
                    st.rerun()
            with c3:
                if st.button("📋 Test Papers", key=f"t_tp_{s['id']}", use_container_width=True):
                    st.session_state.teacher_selected_student_id = s["id"]
                    st.session_state.teacher_student_section = "test_papers"
                    st.rerun()
            with c4:
                if st.button("📤 Submissions", key=f"t_sub_{s['id']}", use_container_width=True):
                    st.session_state.teacher_selected_student_id = s["id"]
                    st.session_state.teacher_student_section = "submissions"
                    st.rerun()

    _section_assign_students()


def _section_assign_students():
    """Let teacher assign or unassign students."""
    st.divider()
    st.subheader("Assign students")
    r_all = get("/profiles/?role=student")
    r_mine = get("/profiles/me/students/")
    if r_all.status_code != 200:
        st.caption("Could not load student list.")
        return
    all_students = r_all.json()
    assigned = {p["id"] for p in (r_mine.json() if r_mine.status_code == 200 else [])}
    for s in all_students:
        name = _student_display_name(s)
        sid = s["id"]
        if sid in assigned:
            if st.button(f"Unassign {name}", key=f"unassign_{sid}"):
                r = post(f"/profiles/{sid}/unassign/", json={})
                if r.status_code == 204:
                    st.rerun()
                else:
                    st.error(r.json().get("detail", r.text) or "Failed to unassign")
        else:
            if st.button(f"Assign {name}", key=f"assign_{sid}"):
                r = post("/profiles/assign-student/", json={"student_id": sid})
                if r.status_code in (200, 201):
                    st.rerun()
                else:
                    st.error(r.json().get("detail", r.text))


def _upload_material_form(default_target_student_ids=None, key_suffix=""):
    """Upload material form; optional target_students (list of profile ids)."""
    r_students = get("/profiles/me/students/")
    assigned_students = r_students.json() if r_students.status_code == 200 else []
    student_options = {_student_display_name(p): p["id"] for p in assigned_students}

    with st.form(f"upload_material_{key_suffix}"):
        title = st.text_input("Title", key=f"um_title_{key_suffix}")
        material_type = st.selectbox("Type", ["note", "worksheet", "question_paper"], key=f"um_type_{key_suffix}")
        description = st.text_area("Description (optional)", key=f"um_desc_{key_suffix}")
        file = st.file_uploader("File", key=f"um_file_{key_suffix}")
        target_labels = list(student_options.keys()) if student_options else []
        default_labels = [
            label for label, pid in student_options.items()
            if pid in (default_target_student_ids or [])
        ] if default_target_student_ids and student_options else []
        selected_labels = st.multiselect(
            "For students (leave empty = all your students)",
            options=target_labels,
            default=default_labels,
            key=f"um_targets_{key_suffix}",
        )
        if st.form_submit_button("Upload"):
            if not title or not file:
                st.error("Title and file required.")
            else:
                target_ids = [student_options[l] for l in selected_labels]
                data = {
                    "title": title,
                    "material_type": material_type,
                    "description": description or "",
                    "accepts_submissions": material_type != "note",
                }
                if target_ids:
                    data["target_students"] = ",".join(map(str, target_ids))
                files = {"file": (file.name, file.getvalue())}
                r = post("/materials/", data=data, files=files)
                if r.status_code == 201:
                    st.success("Uploaded.")
                    st.rerun()
                else:
                    try:
                        err = r.json()
                        msg = err.get("detail", err) if isinstance(err, dict) else err
                        if isinstance(msg, dict):
                            msg = " ".join(f"{k}: {v}" for k, v in msg.items())
                    except Exception:
                        msg = r.text or f"HTTP {r.status_code}"
                    st.error(f"Upload failed: {msg}")


def _render_student_submissions_for_teacher(profile_id):
    r = get(f"/profiles/{profile_id}/submissions/")
    if r.status_code != 200:
        st.error("Could not load this student's submissions.")
        return
    subs = r.json()
    if not subs:
        st.info("This student has not submitted any answers yet.")
        return
    for s in subs:
        with st.container():
            st.markdown(f"**{s.get('material_title')}** ({s.get('material_type', '').replace('_', ' ')})")
            st.caption(f"Submitted: {s.get('submitted_at', '')}")
            if s.get("answer_file_url"):
                st.markdown(f"[Download answer]({s['answer_file_url']})")
            if s.get("note"):
                st.caption(s["note"])
            st.divider()


def section_my_personal_notes_teacher(materials):
    """Teacher's own notes: view and upload notes only."""
    notes = [m for m in materials if m["material_type"] == "note"]
    st.subheader("My Personal Notes")
    if not notes:
        st.info("No notes yet. Upload one below.")
    else:
        for m in notes:
            with st.expander(m["title"]):
                if m.get("description"):
                    st.caption(m["description"])
                if m.get("file_url"):
                    st.markdown(f"[Download]({m['file_url']})")
    st.markdown("---")
    with st.expander("Upload new note"):
        with st.form("upload_note_teacher"):
            title_in = st.text_input("Title")
            description = st.text_area("Description (optional)")
            file = st.file_uploader("File")
            if st.form_submit_button("Upload"):
                if not title_in or not file:
                    st.error("Title and file required.")
                else:
                    files = {"file": (file.name, file.getvalue())}
                    data = {
                        "title": title_in,
                        "material_type": "note",
                        "description": description or "",
                        "accepts_submissions": False,
                    }
                    r = post("/materials/", data=data, files=files)
                    if r.status_code == 201:
                        st.success("Uploaded.")
                        st.rerun()
                    else:
                        try:
                            err = r.json()
                            msg = err.get("detail", err) if isinstance(err, dict) else err
                            if isinstance(msg, dict):
                                msg = " ".join(f"{k}: {v}" for k, v in msg.items())
                        except Exception:
                            msg = r.text or f"HTTP {r.status_code}"
                        st.error(f"Upload failed: {msg}")



def teacher_home():
    profile = st.session_state.profile
    section = st.session_state.section

    if section == "edit_profile":
        render_profile_header(profile, is_teacher=True)
        return
    render_profile_header(profile, is_teacher=True)

    r = get("/materials/")
    materials = r.json() if r.status_code == 200 else []
    section = st.session_state.section

    if section == "my_students":
        st.subheader("My Students")
        section_my_students_teacher(materials)
    elif section == "my_personal_notes":
        st.subheader("My Materials")
        section_my_personal_notes_teacher(materials)
        st.markdown("---")
        st.subheader("Upload material")
        _upload_material_form(key_suffix="main")
        st.markdown("---")
        st.subheader("All materials & submissions")
        for m in materials:
            with st.expander(f"{m['material_type'].replace('_', ' ').title()}: {m['title']}"):
                if m.get("file_url"):
                    st.markdown(f"[Download]({m['file_url']})")
                targets = m.get("target_students") or []
                if targets:
                    st.caption(f"For {len(targets)} student(s)")
                if m.get("accepts_submissions"):
                    r_subs = get(f"/materials/{m['id']}/submissions/")
                    if r_subs.status_code == 200:
                        subs = r_subs.json()
                        st.write(f"**{len(subs)} submission(s)**")
                        for s in subs:
                            st.write(f"- **{s.get('student_name')}** — {s.get('submitted_at', '')}")
                            if s.get("answer_file_url"):
                                st.markdown(f"  [Download answer]({s['answer_file_url']})")
                    else:
                        st.write("No submissions yet.")
                else:
                    st.caption("Does not accept submissions.")
        r_students = get("/profiles/me/students/")
        if r_students.status_code == 200:
            st.caption("**Assigned students:** " + ", ".join(_student_display_name(p) for p in r_students.json()))
    else:
        st.subheader("Dashboard")
        st.markdown("Use the sidebar to open **My Students** or **My Materials**.")
        r_students = get("/profiles/me/students/")
        if r_students.status_code == 200:
            count = len(r_students.json())
            st.info(f"You have **{count}** assigned student(s). Go to **My Students** to manage them or upload materials.")
        else:
            st.info("Go to **My Students** to assign students and upload materials.")



def _render_sidebar_nav(profile):
    """Sidebar navigation: one active section, rest are buttons."""
    is_teacher = profile.get("role") == "teacher"
    section = st.session_state.section

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Navigation**")

    if is_teacher:
        nav_items = [
            ("my_students", "👥 My Students", "My Students"),
            ("my_personal_notes", "📝 My Materials", "My Materials"),
        ]
    else:
        nav_items = [
            ("notes", "📝 Notes", "Notes"),
            ("worksheets", "📄 Worksheets", "Worksheets"),
            ("test_papers", "📋 Test Papers", "Test Papers"),
            ("my_submissions", "📤 My Submissions", "My Submissions"),
        ]

    for key, label, _ in nav_items:
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.section = key
            if is_teacher:
                st.session_state.teacher_selected_student_id = None
                st.session_state.teacher_student_section = None
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("✏️ Edit profile", key="nav_edit_profile", use_container_width=True):
        st.session_state.section = "edit_profile"
        st.rerun()


def main():
    st.set_page_config(
        page_title="Tutorial Center",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_app_css()
    ensure_token()

    # Restore session from URL (survives page reload)
    try:
        q = st.query_params
        token_from_url = q.get("token")
    except Exception:
        token_from_url = None
    if token_from_url and st.session_state.token is None:
        st.session_state.token = token_from_url
        r = get("/profile/me/")
        if r.status_code == 200:
            st.session_state.profile = r.json()
            st.rerun()
        else:
            st.session_state.token = None

    if st.session_state.token is None:
        if st.query_params.get("error"):
            st.toast(f"Sign-in issue: {st.query_params.get('error')}", icon="⚠️")
        # Google redirect (commented out for now)
        # redirect_url = st.session_state.get("pending_google_redirect")
        # if redirect_url:
        #     st.session_state.pending_google_redirect = None
        #     safe_url = html.escape(redirect_url)
        #     st.markdown(
        #         f'<meta http-equiv="refresh" content="0;url={safe_url}">'
        #         f'<p style="text-align:center;margin-top:2rem;">Redirecting to Google…</p>',
        #         unsafe_allow_html=True,
        #     )
        #     st.stop()
        _render_auth_page()
        return

    profile = st.session_state.profile
    if not profile:
        r = get("/profile/me/")
        if r.status_code == 200:
            st.session_state.profile = r.json()
            st.rerun()
        else:
            st.error("Session invalid. Please log in again.")
            logout()
            return

    # Sidebar: user info + nav
    st.sidebar.markdown("### 📚 Tutorial Center")
    st.sidebar.markdown(f"**{get_display_name(profile)}**")
    st.sidebar.caption("Teacher" if profile.get("role") == "teacher" else "Student")
    _render_sidebar_nav(profile)
    if st.sidebar.button("🚪 Log out", key="sidebar_logout", use_container_width=True):
        logout()

    # Main: top bar (optional greeting) + content
    col_main, col_user = st.columns([5, 1])
    with col_user:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log out", key="main_logout"):
            logout()

    with col_main:
        if profile.get("role") == "student":
            student_home()
        else:
            teacher_home()


def _render_auth_page():
    """Centered auth card with brand header."""
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            '<div class="brand-block">'
            '<h1>📚 Tutorial Center</h1>'
            '<p>Sign in or create an account to continue</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        tab1, tab2 = st.tabs(["Sign in", "Register"])
        with tab1:
            login_form()
        with tab2:
            register_form()


if __name__ == "__main__":
    main()