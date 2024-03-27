import logging
import tempfile
from contextlib import contextmanager
from urllib.parse import urlparse

from django import forms
from django.conf import settings

from .exceptions import SynchronisationError
from .utils import register_data_backend

__all__ = ("LocalBackend", "GitRepositoryBackend")

logger = logging.getLogger("peering.manager.core.data_backends")


class DataBackend:
    """
    A data backend represents a system used to record data like, for instance, a git
    repository.
    """

    is_local = False
    parameters = {}
    sensitive_parameters = []
    do_not_call_in_template = True

    def __init__(self, url, **kwargs):
        self.url = url
        self.params = kwargs
        self.config = self.init_config()

    @property
    def url_scheme(self):
        return urlparse(self.url).scheme.lower()

    @contextmanager
    def fetch(self):
        """
        A context manager which is supposed to:

        1. Handle setup and synchronisation
        2. Yield the local path at which data has been replicated
        3. Perform required cleanup if any
        """
        return NotImplementedError()

    def init_config(self):
        return


@register_data_backend()
class LocalBackend(DataBackend):
    name = "local"
    label = "Local"
    is_local = True

    @contextmanager
    def fetch(self):
        logger.debug("local data source type; skipping fetch")
        yield urlparse(self.url).path


@register_data_backend()
class GitRepositoryBackend(DataBackend):
    name = "git"
    label = "Git"
    parameters = {
        "username": forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
            label="Username",
            help_text="Only used for cloning with HTTP(S)",
        ),
        "password": forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
            label="Password",
            help_text="Only used for cloning with HTTP(S)",
        ),
        "branch": forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
            label="Branch",
        ),
    }
    sensitive_parameters = ["password"]

    def init_config(self):
        from dulwich.config import ConfigDict

        config = ConfigDict()

        if settings.HTTP_PROXIES and self.url_scheme in settings.HTTP_PROXIES:
            config.set("http", "proxy", settings.HTTP_PROXIES[self.url_scheme])

        return config

    @contextmanager
    def fetch(self):
        from dulwich import porcelain

        local_path = tempfile.TemporaryDirectory()
        clone_args = {
            "branch": self.params.get("branch"),
            "config": self.config,
            "depth": 1,
            "errstream": porcelain.NoneStream(),
            "quiet": True,
        }

        if self.url_scheme in ("http", "https"):
            if self.params.get("username"):
                clone_args.update(
                    {
                        "username": self.params.get("username"),
                        "password": self.params.get("password"),
                    }
                )

        logger.debug(f"cloning git repository: {self.url}")
        try:
            porcelain.clone(self.url, local_path.name, **clone_args)
        except BaseException as e:
            raise SynchronisationError(
                f"Fetching remote data failed ({type(e).__name__})"
            ) from e

        yield local_path.name

        local_path.cleanup()
