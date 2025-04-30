from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "messaging"
urlpatterns = [
    path(
        "contacts/",
        include(
            get_model_urls(app_label="messaging", model_name="contact", detail=False)
        ),
    ),
    path(
        "contacts/<int:pk>/",
        include(get_model_urls(app_label="messaging", model_name="contact")),
    ),
    path(
        "contact-roles/",
        include(
            get_model_urls(
                app_label="messaging", model_name="contactrole", detail=False
            )
        ),
    ),
    path(
        "contact-roles/<int:pk>/",
        include(get_model_urls(app_label="messaging", model_name="contactrole")),
    ),
    path(
        "contact-assignments/",
        include(
            get_model_urls(
                app_label="messaging", model_name="contactassignment", detail=False
            )
        ),
    ),
    path(
        "contact-assignments/<int:pk>/",
        include(get_model_urls(app_label="messaging", model_name="contactassignment")),
    ),
    path(
        "emails/",
        include(
            get_model_urls(app_label="messaging", model_name="email", detail=False)
        ),
    ),
    path(
        "emails/<int:pk>/",
        include(get_model_urls(app_label="messaging", model_name="email")),
    ),
]
