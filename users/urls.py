from django.conf.urls import url

from . import views

app_name = "users"
urlpatterns = [
    url(r"^profile/$", views.ProfileView.as_view(), name="profile"),
    url(r"^password/$", views.ChangePasswordView.as_view(), name="change_password"),
]
