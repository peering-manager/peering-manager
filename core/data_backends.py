import io
import logging
import tempfile
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from django import forms
from django.conf import settings
from dulwich import porcelain
from dulwich.config import ConfigDict

from .constants import GIT_ERROR_MATCHES
from .exceptions import FetchError, PushError, SynchronisationError
from .utils import register_data_backend

__all__ = ("GitRepositoryBackend", "LocalBackend")

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
        path = Path(self.url).resolve()

        if not path.exists():
            raise FetchError(f"Local path does not exist: {path}")

        yield str(path)

    @contextmanager
    def push(self, *file_paths, commit_message=settings.GIT_COMMIT_MESSAGE):
        logger.debug("local data source type; skipping push")
        path = Path(self.url).resolve()

        if not path.exists():
            raise PushError(f"Local path does not exist: {path}")

        yield str(path)


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

        if settings.HTTP_PROXIES and (
            proxy := settings.HTTP_PROXIES.get(self.url_scheme, None)
        ):
            config.set("http", "proxy", proxy)

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
            porcelain.clone(source=self.url, target=local_path.name, **clone_args)
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

            changes = porcelain.get_tree_changes(repo=local_path)
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
                # Fetch stderr to catch errors not raising exceptions
                errstream = io.BytesIO()
                porcelain.push(
                    repo=local_path,
                    remote_location=self.url,
                    refspecs=self.params.get("branch") or "main",
                    errstream=errstream,
                    **auth_args,
                )

                # This does not feel really robust, but that's the best we can do
                if err := errstream.getvalue().decode(errors="replace"):
                    err_output = unicodedata.normalize("NFKC", err).replace(
                        "\u0000", ""
                    )
                    if any(match in err_output for match in GIT_ERROR_MATCHES):
                        raise PushError(err_output)
            except BaseException as e:
                raise PushError(
                    f"Pushing to remote failed ({type(e).__name__}): {e!s}"
                ) from e
