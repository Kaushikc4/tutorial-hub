from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path("register/", csrf_exempt(views.RegisterView.as_view())),
    path("login/", csrf_exempt(views.LoginView.as_view())),
    # path("auth/google/", views.GoogleAuthURLView.as_view()),
    # path("auth/google/callback/", views.google_callback_view),
    path("profile/me/", views.MyProfileView.as_view()),
    path("profiles/", views.ProfileListView.as_view()),
    path("profiles/me/students/", views.MyAssignedStudentsView.as_view()),
    path("profiles/assign-student/", views.AssignStudentView.as_view()),
    path("profiles/<int:profile_id>/unassign/", views.UnassignStudentView.as_view()),
    path("materials/", views.MaterialListCreateView.as_view()),
    path("materials/<int:pk>/", views.MaterialDetailView.as_view()),
    path("submissions/me/", views.MySubmissionsView.as_view()),
    path("materials/<int:material_id>/submissions/", views.SubmissionsByMaterialView.as_view()),
    path("profiles/<int:profile_id>/submissions/", views.SubmissionsByStudentView.as_view()),
]