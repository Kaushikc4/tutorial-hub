import os
import secrets

import requests
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .choices import RoleChoice
from .models import Material, Profile, StudentSubmission, TeacherStudent
from .serializer import (
    MaterialCreateSerializer,
    MaterialSerializer,
    ProfileSerializer,
    StudentSubmissionCreateSerializer,
    StudentSubmissionSerializer,
)


def _get_user_by_username_or_email(identifier):
    """Return User if identifier is username or email; else None."""
    identifier = (identifier or "").strip()
    if not identifier:
        return None
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()
    return User.objects.filter(username__iexact=identifier).first()


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """Return auth token for username/email + password. CSRF-exempt for Streamlit/Postman."""
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        # Support both form (data=) and JSON (json=) from clients
        data = getattr(request, "data", None) or request.POST
        username_or_email = (
            (data.get("username") or data.get("email") or "").strip()
            if data else ""
        )
        password = (data.get("password") or "") if data else ""
        if not username_or_email or not password:
            return Response(
                {"detail": "Username/email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = _get_user_by_username_or_email(username_or_email)
        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid username/email or password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(APIView):
    """Register with username and password; optional email. Or use Google sign-in."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password")
        role = (request.data.get("role") or "student").lower().strip()
        full_name = (request.data.get("full_name") or "").strip()
        if not username or not password:
            return Response(
                {"detail": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if role not in (RoleChoice.STUDENT, RoleChoice.TEACHER):
            role = RoleChoice.STUDENT
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"detail": "A user with that username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email and User.objects.filter(email__iexact=email).exists():
            return Response(
                {"detail": "A user with that email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(username=username, password=password, email=email or "")
        profile = Profile.objects.create(user=user, role=role, full_name=full_name or username)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "profile": ProfileSerializer(profile).data,
        }, status=status.HTTP_201_CREATED)
    

class MyProfileView(APIView):
    """Get or update current user's tutorial profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileListView(APIView):
    """List profiles (students and teachers)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Profile.objects.all().select_related("user")
        role = request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return Response(ProfileSerializer(qs, many=True).data)
    

def _materials_visible_to_student(profile):
    """Materials visible to this student: uploaded by one of their teachers, and (no target_students or student in target_students)."""
    my_teacher_ids = TeacherStudent.objects.filter(student=profile).values_list("teacher_id", flat=True)
    return (
        Material.objects.filter(uploaded_by_id__in=my_teacher_ids)
        .annotate(n_targets=Count("target_students"))
        .filter(Q(n_targets=0) | Q(target_students=profile))
        .distinct()
    )


class MaterialListCreateView(APIView):
    """List materials (filter by type), or create teacher's only."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if profile.is_student:
            materials = _materials_visible_to_student(profile)
        else:
            materials = Material.objects.filter(uploaded_by=profile)
        materials = materials.select_related("uploaded_by").prefetch_related("target_students")
        material_type = request.query_params.get("type")
        if material_type:
            materials = materials.filter(material_type=material_type)
        serializer = MaterialSerializer(materials, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher:
            return Response(
                {"detail": "Only teachers can upload materials."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Build a plain dict so target_students is always a list of PKs (QueryDict can corrupt list values)
        raw_ts = request.data.get("target_students")
        if raw_ts is None or raw_ts == "":
            target_students_ids = []
        elif isinstance(raw_ts, str):
            raw = (raw_ts or "").strip()
            try:
                target_students_ids = [int(x) for x in raw.split(",") if x.strip()] if raw else []
            except ValueError:
                target_students_ids = []
        elif isinstance(raw_ts, list):
            try:
                target_students_ids = [int(x) for x in raw_ts if str(x).strip()]
            except (ValueError, TypeError):
                target_students_ids = []
        else:
            target_students_ids = []

        payload = {
            "title": request.data.get("title"),
            "material_type": request.data.get("material_type"),
            "description": request.data.get("description") or "",
            "accepts_submissions": request.data.get("accepts_submissions"),
            "target_students": target_students_ids,
        }
        payload["file"] = request.data.get("file") or request.FILES.get("file")
        serializer = MaterialCreateSerializer(data=payload)
        if serializer.is_valid():
            target_students = serializer.validated_data.get("target_students") or []
            assigned_ids = set(
                TeacherStudent.objects.filter(teacher=profile).values_list("student_id", flat=True)
            )
            for s in target_students:
                if s.id not in assigned_ids:
                    return Response(
                        {"detail": f"Student profile id {s.id} is not assigned to you."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            serializer.save(uploaded_by=profile)
            return Response(
                MaterialSerializer(serializer.instance, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _material_visible_to_student(material, profile):
    """True if this material is visible to this student."""
    if not profile.is_student:
        return True
    my_teacher_ids = TeacherStudent.objects.filter(student=profile).values_list("teacher_id", flat=True)
    if material.uploaded_by_id not in list(my_teacher_ids):
        return False
    n = material.target_students.count()
    return n == 0 or material.target_students.filter(pk=profile.pk).exists()


class MaterialDetailView(APIView):
    """Retrieve or Delete a material (teacher can delete own)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        material = get_object_or_404(Material, pk=pk)
        profile = get_object_or_404(Profile, user=request.user)
        if profile.is_student and not _material_visible_to_student(material, profile):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = MaterialSerializer(material, context={"request": request})
        return Response(serializer.data)
    
    def delete(self, request, pk):
        material = get_object_or_404(Material, pk=pk)
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher or material.uploaded_by_id != profile.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        material.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class MySubmissionsView(APIView):
    """List current student's submissions, create new submissions."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_student:
            return Response({"detail": "Only students have submissions."}, status=status.HTTP_403_FORBIDDEN)
        subs = StudentSubmission.objects.filter(student=profile).select_related("material")
        serializer = StudentSubmissionSerializer(subs, many=True, context={"request": request})
        return Response(serializer.data)
    
    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_student:
            return Response({"detail": "Only students can submit answers."}, status=status.HTTP_403_FORBIDDEN)
        serializer = StudentSubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            material = serializer.validated_data["material"]
            if not _material_visible_to_student(material, profile):
                return Response(
                    {"detail": "You do not have access to this material."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if not material.accepts_submissions:
                return Response(
                    {"detail": "This material does not accept submissions."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if StudentSubmission.objects.filter(material=material, student=profile).exists():
                return Response(
                    {"detail": "You have already submitted an answer for this material."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save(student=profile)
            return Response(
                StudentSubmissionSerializer(serializer.instance, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmissionsByMaterialView(APIView):
    """List all submissions for a material (teachers only; material must be yours)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, material_id):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher:
            return Response(status=status.HTTP_403_FORBIDDEN)
        material = get_object_or_404(Material, pk=material_id)
        if material.uploaded_by_id != profile.id:
            return Response({"detail": "This material is not yours."}, status=status.HTTP_404_NOT_FOUND)
        subs = StudentSubmission.objects.filter(material=material).select_related("student", "student__user")
        serializer = StudentSubmissionSerializer(subs, many=True, context={"request": request})
        return Response(serializer.data)


class SubmissionsByStudentView(APIView):
    """List all submissions for a given student (teachers only; student must be assigned to you)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, profile_id):
        teacher_profile = get_object_or_404(Profile, user=request.user)
        if not teacher_profile.is_teacher:
            return Response(status=status.HTTP_403_FORBIDDEN)
        student_profile = get_object_or_404(Profile, pk=profile_id)
        if not student_profile.is_student:
            return Response(
                {"detail": "Profile is not a student."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not TeacherStudent.objects.filter(teacher=teacher_profile, student=student_profile).exists():
            return Response({"detail": "This student is not assigned to you."}, status=status.HTTP_404_NOT_FOUND)
        subs = StudentSubmission.objects.filter(student=student_profile).select_related("material")
        serializer = StudentSubmissionSerializer(subs, many=True, context={"request": request})
        return Response(serializer.data)


class MyAssignedStudentsView(APIView):
    """List students assigned to the current teacher."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher:
            return Response({"detail": "Only teachers have assigned students."}, status=status.HTTP_403_FORBIDDEN)
        qs = Profile.objects.filter(
            id__in=TeacherStudent.objects.filter(teacher=profile).values_list("student_id", flat=True)
        ).select_related("user")
        return Response(ProfileSerializer(qs, many=True).data)


class AssignStudentView(APIView):
    """Assign a student to the current teacher (teacher only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher:
            return Response({"detail": "Only teachers can assign students."}, status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get("student_id") or request.data.get("student")
        if not student_id:
            return Response({"detail": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        student = get_object_or_404(Profile, pk=student_id)
        if not student.is_student:
            return Response({"detail": "Profile is not a student."}, status=status.HTTP_400_BAD_REQUEST)
        _, created = TeacherStudent.objects.get_or_create(teacher=profile, student=student)
        return Response(
            ProfileSerializer(student).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UnassignStudentView(APIView):
    """Remove a student from the current teacher's list (teacher only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, profile_id):
        profile = get_object_or_404(Profile, user=request.user)
        if not profile.is_teacher:
            return Response({"detail": "Only teachers can unassign students."}, status=status.HTTP_403_FORBIDDEN)
        deleted, _ = TeacherStudent.objects.filter(teacher=profile, student_id=profile_id).delete()
        if not deleted:
            return Response({"detail": "Student was not assigned to you."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Google Sign-In (OAuth 2.0) — commented out for now ─────────────────────

# GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
#
#
# @method_decorator(csrf_exempt, name="dispatch")
# class GoogleAuthURLView(APIView):
#     """GET: return the Google OAuth URL for the frontend to redirect the user to."""
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
#         if not client_id:
#             return Response(
#                 {"detail": "Google Sign-In is not configured (missing GOOGLE_OAUTH_CLIENT_ID)."},
#                 status=status.HTTP_503_SERVICE_UNAVAILABLE,
#             )
#         base_url = request.build_absolute_uri("/").rstrip("/")
#         redirect_uri = f"{base_url}api/tutorial/auth/google/callback/"
#         state = secrets.token_urlsafe(32)
#         request.session["google_oauth_state"] = state
#         url = (
#             "https://accounts.google.com/o/oauth2/v2/auth"
#             f"?client_id={client_id}"
#             f"&redirect_uri={redirect_uri}"
#             "&response_type=code"
#             "&scope=openid email profile"
#             f"&state={state}"
#             "&access_type=offline"
#             "&prompt=consent"
#         )
#         return Response({"url": url})
#
#
# def _google_callback_view(request):
#     """Exchange code for tokens, get or create user, redirect to frontend with token."""
#     client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
#     client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
#     frontend_url = (os.environ.get("TUTORIAL_FRONTEND_URL") or "http://localhost:8501").rstrip("/")
#
#     if not client_id or not client_secret:
#         return redirect(f"{frontend_url}?error=google_not_configured")
#
#     code = request.GET.get("code")
#     state = request.GET.get("state")
#     if not code:
#         return redirect(f"{frontend_url}?error=missing_code")
#
#     saved_state = request.session.get("google_oauth_state")
#     if state != saved_state:
#         return redirect(f"{frontend_url}?error=invalid_state")
#     if saved_state:
#         del request.session["google_oauth_state"]
#
#     base_url = request.build_absolute_uri("/").rstrip("/")
#     redirect_uri = f"{base_url}api/tutorial/auth/google/callback/"
#
#     token_resp = requests.post(
#         "https://oauth2.googleapis.com/token",
#         data={
#             "client_id": client_id,
#             "client_secret": client_secret,
#             "code": code,
#             "grant_type": "authorization_code",
#             "redirect_uri": redirect_uri,
#         },
#         headers={"Content-Type": "application/x-www-form-urlencoded"},
#         timeout=10,
#     )
#     if token_resp.status_code != 200:
#         return redirect(f"{frontend_url}?error=token_exchange_failed")
#
#     access_token = token_resp.json().get("access_token")
#     if not access_token:
#         return redirect(f"{frontend_url}?error=no_token")
#
#     userinfo_resp = requests.get(
#         "https://www.googleapis.com/oauth2/v2/userinfo",
#         headers={"Authorization": f"Bearer {access_token}"},
#         timeout=10,
#     )
#     if userinfo_resp.status_code != 200:
#         return redirect(f"{frontend_url}?error=userinfo_failed")
#
#     info = userinfo_resp.json()
#     email = (info.get("email") or "").strip()
#     name = (info.get("name") or "").strip()
#     if not email:
#         return redirect(f"{frontend_url}?error=no_email")
#
#     user = User.objects.filter(email__iexact=email).first()
#     if not user:
#         username = email.split("@")[0]
#         base_username = username
#         idx = 0
#         while User.objects.filter(username=username).exists():
#             idx += 1
#             username = f"{base_username}{idx}"
#         user = User.objects.create_user(username=username, email=email, password=None)
#         user.set_unusable_password()
#         user.save()
#         Profile.objects.get_or_create(
#             user=user,
#             defaults={"role": RoleChoice.STUDENT, "full_name": name or username},
#         )
#
#     token, _ = Token.objects.get_or_create(user=user)
#     return redirect(f"{frontend_url}?token={token.key}")
#
#
# @csrf_exempt
# def google_callback_view(request):
#     """Wrapper so Django URL can call the callback with CSRF exempt."""
#     return _google_callback_view(request)
