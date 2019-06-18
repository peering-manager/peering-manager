from django.conf.urls import re_path

from . import views

app_name = "users"
urlpatterns = [
    re_path(r"^profile/$", views.ProfileView.as_view(), name="profile"),
    re_path(r"^password/$", views.ChangePasswordView.as_view(), name="change_password"),
    re_path(r"^api-tokens/$", views.TokenList.as_view(), name="token_list"),
    re_path(r"^api-tokens/add/$", views.TokenAddEdit.as_view(), name="token_add"),
    re_path(
        r"^api-tokens/(?P<pk>\d+)/edit/$",
        views.TokenAddEdit.as_view(),
        name="token_edit",
    ),
    re_path(
        r"^api-tokens/(?P<pk>\d+)/delete/$",
        views.TokenDelete.as_view(),
        name="token_delete",
    ),
]
