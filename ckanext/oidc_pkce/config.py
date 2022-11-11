from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan.exceptions import CkanConfigurationException


CONFIG_BASE_URL = "ckanext.oidc_pkce.base_url"
CONFIG_CLIENT_ID = "ckanext.oidc_pkce.client_id"

CONFIG_AUTH_PATH = "ckanext.oidc_pkce.auth_path"
DEFAULT_AUTH_PATH = "/oauth2/default/v1/authorize"

CONFIG_TOKEN_PATH = "ckanext.oidc_pkce.token_path"
DEFAULT_TOKEN_PATH = "/oauth2/default/v1/token"

CONFIG_USERINFO_PATH = "ckanext.oidc_pkce.userinfo_path"
DEFAULT_USERINFO_PATH = "/oauth2/default/v1/userinfo"

CONFIG_REDIRECT_PATH = "ckanext.oidc_pkce.redirect_path"
DEFAULT_REDIRECT_PATH = "/user/login/oidc-pkce/callback"

CONFIG_SCOPE = "ckanext.oidc_pkce.scope"
DEFAULT_SCOPE = "openid email profile"

CONFIG_SAME_ID = "ckanext.oidc_pkce.use_same_id"
DEFAULT_SAME_ID = False

CONFIG_MUNGE_PASSWORD = "ckanext.oidc_pkce.munge_password"
DEFAULT_MUNGE_PASSWORD = False


def scope() -> str:
    return tk.config.get(CONFIG_SCOPE, DEFAULT_SCOPE)


def same_id() -> bool:
    return tk.asbool(tk.config.get(CONFIG_SAME_ID, DEFAULT_SAME_ID))


def client_id() -> str:
    id_ = tk.config.get(CONFIG_CLIENT_ID)
    if not id_:
        raise CkanConfigurationException(f"{CONFIG_CLIENT_ID} must be configured")

    return id_


def auth_path() -> str:

    return tk.config.get(CONFIG_AUTH_PATH, DEFAULT_AUTH_PATH)


def token_path() -> str:
    return tk.config.get(CONFIG_TOKEN_PATH, DEFAULT_TOKEN_PATH)


def redirect_path() -> str:
    return tk.config.get(CONFIG_REDIRECT_PATH, DEFAULT_REDIRECT_PATH)


def userinfo_path() -> str:
    return tk.config.get(CONFIG_USERINFO_PATH, DEFAULT_USERINFO_PATH)


def redirect_url() -> str:
    return tk.config["ckan.site_url"].rstrip("/") + redirect_path()


def userinfo_url() -> str:
    return base_url() + userinfo_path()


def base_url() -> str:
    url = tk.config.get(CONFIG_BASE_URL, None)
    if not url:
        raise CkanConfigurationException(f"{CONFIG_BASE_URL} must be configured")

    return url.rstrip("/")


def auth_url() -> str:
    return base_url() + auth_path()


def token_url() -> str:
    return base_url() + token_path()


def munge_password() -> bool:
    return tk.asbool(tk.config.get(CONFIG_MUNGE_PASSWORD, DEFAULT_MUNGE_PASSWORD))
