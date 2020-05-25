from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("preferences/", views.PreferencesView.as_view(), name="preferences"),
    path("password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("api-tokens/", views.TokenList.as_view(), name="token_list"),
    path("api-tokens/add/", views.TokenAddEdit.as_view(), name="token_add"),
    path("api-tokens/<int:pk>/edit/", views.TokenAddEdit.as_view(), name="token_edit"),
    path(
        "api-tokens/<int:pk>/delete/", views.TokenDelete.as_view(), name="token_delete"
    ),
]
