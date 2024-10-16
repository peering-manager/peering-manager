import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from django import forms
from django.conf import settings
from dulwich import porcelain
from dulwich.config import ConfigDict

from .exceptions import PushError, SynchronisationError
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

    @contextmanager
    def push(self, *file_paths, commit_message=settings.GIT_COMMIT_MESSAGE):
        """
        A context manager which is supposed to:

        1. Handle setup and push
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

    @contextmanager
    def push(self, *file_paths, commit_message=settings.GIT_COMMIT_MESSAGE):
        yield urlparse(self.url).path
        logger.debug("local data source type; skipping push")


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
        config = ConfigDict()

        if settings.HTTP_PROXIES and self.url_scheme in settings.HTTP_PROXIES:
            config.set("http", "proxy", settings.HTTP_PROXIES[self.url_scheme])

        return config

    @contextmanager
    def fetch(self):
        local_path = tempfile.TemporaryDirectory()
        clone_args = {
            "branch": self.params.get("branch"),
            "config": self.config,
            "depth": 1,
            "errstream": porcelain.NoneStream(),
            "quiet": True,
        }

        if self.url_scheme in ("http", "https") and self.params.get("username"):
            clone_args.update(
                {
                    "username": self.params.get("username"),
                    "password": self.params.get("password"),
                }
            )

        logger.debug(f"cloning git repository: {self.url}")
        try:
            porcelain.clone(self.url, target=local_path.name, **clone_args)
        except BaseException as e:
            raise SynchronisationError(
                f"Fetching remote data failed ({type(e).__name__})"
            ) from e

        yield local_path.name

        local_path.cleanup()

    @contextmanager
    def push(self, *file_paths, commit_message=settings.GIT_COMMIT_MESSAGE):
        # Fetch the repository first, and yield immediatly to let changes happen
        with self.fetch() as local_path:
            yield local_path

            auth_args = {}

            if self.url_scheme in ("http", "https") and self.params.get("username"):
                auth_args = {
                    "username": self.params.get("username"),
                    "password": self.params.get("password"),
                }

            paths = []
            for file_path in file_paths:
                paths.append(str(Path(local_path, file_path)))

            logger.debug(f"staging files for git repository: {self.url}")
            added, ignored = porcelain.add(repo=local_path, paths=paths)

            changes = porcelain.get_tree_changes(local_path)
            if all(not v for v in changes.values()):
                logger.debug(f"no changes found for git repository: {self.url}")
                return

            logger.debug(
                f"staged {added}, ignored {list(ignored)} for git repository: {self.url}"
            )
            commit_sha = porcelain.commit(
                repo=local_path,
                message=commit_message,
                author=settings.GIT_COMMIT_AUTHOR,
            )

            logger.debug(
                f"pushing commit {commit_sha.decode()} to remote git repository: {self.url}"
            )
            try:
                porcelain.push(
                    local_path,
                    remote_location=self.url,
                    refspecs=self.params.get("branch") or "main",
                    **auth_args,
                )
            except BaseException as e:
                raise PushError(f"Pushing to remote failed ({type(e).__name__})") from e
