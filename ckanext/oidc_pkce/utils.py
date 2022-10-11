from __future__ import annotations

import hashlib
import base64
import secrets
import logging
from typing import Any, Optional

from ckan import model
from ckan.common import session
from ckan.plugins import PluginImplementations

from .interfaces import IOidcPkce

log = logging.getLogger(__name__)

DEFAULT_LENGTH = 64
SESSION_USER = "ckanext:oidc-pkce:username"


def code_verifier(n_bytes: int = DEFAULT_LENGTH) -> str:
    """Generate PKCE verifier"""
    valid_range = range(31, 97)
    if n_bytes not in valid_range:
        raise ValueError(f"Verifier too short. n_bytes must in {valid_range}")

    return secrets.token_urlsafe(n_bytes)


def code_challenge(verifier: str) -> str:
    """Generate a code challenge based on the code verifier"""
    digest = hashlib.sha256(bytes(verifier, "ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def app_state(n_bytes: int = DEFAULT_LENGTH) -> str:
    return secrets.token_urlsafe(n_bytes)


def sync_user(userinfo: dict[str, Any]) -> Optional[model.User]:
    plugin = next(iter(PluginImplementations(IOidcPkce)))
    log.debug("Synchronize user using %s", plugin)

    user = plugin.get_oidc_user(userinfo)
    if not user:
        log.error("Cannot locate user/create using OIDC info: %s", userinfo)
        return

    return user


def login(user: model.User):
    session[SESSION_USER] = user.name


def logout():
    session.pop(SESSION_USER, None)
