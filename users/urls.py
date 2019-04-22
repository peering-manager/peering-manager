from django.conf.urls import url

from . import views

app_name = "users"
urlpatterns = [
    url(r"^profile/$", views.ProfileView.as_view(), name="profile"),
    url(r"^password/$", views.ChangePasswordView.as_view(), name="change_password"),
    url(r"^api-tokens/$", views.TokenList.as_view(), name="token_list"),
    url(r"^api-tokens/add/$", views.TokenAddEdit.as_view(), name="token_add"),
    url(
        r"^api-tokens/(?P<pk>\d+)/edit/$",
        views.TokenAddEdit.as_view(),
        name="token_edit",
    ),
    url(
        r"^api-tokens/(?P<pk>\d+)/delete/$",
        views.TokenDelete.as_view(),
        name="token_delete",
    ),
]
