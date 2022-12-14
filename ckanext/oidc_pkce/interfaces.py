from __future__ import annotations
import secrets
from typing import Any, Optional

import ckan.plugins.toolkit as tk

from ckan import model
from ckan.plugins import Interface
from ckan.logic.action.create import _get_random_username_from_email

from . import config, signals


class IOidcPkce(Interface):
    """ """

    def get_oidc_user(self, userinfo: dict[str, Any]) -> Optional[model.User]:
        q = model.Session.query(model.User)

        user = q.filter(
            model.User.plugin_extras["oidc_pkce"]["sub"].astext == userinfo["sub"]
        ).one_or_none()

        if user:
            signals.user_exist.send(user.id)
            return user

        user = q.filter_by(email=userinfo["email"]).one_or_none()
        if user:
            admin = tk.get_action("get_site_user")({"ignore_auth": True}, {})
            user_dict = tk.get_action("user_show")({"user": admin["name"]}, {"id": user.id, "include_plugin_extras": True})
            extras = user_dict.pop('plugin_extras', None) or {}

            data = self.oidc_info_into_user_dict(userinfo)
            data["id"] = user.id
            data.pop("name")

            if not config.munge_password():
                data.pop("password")

            extras.update(data["plugin_extras"])
            data["plugin_extras"] = extras

            user_dict.update(data)
            tk.get_action("user_update")({"user": admin["name"]}, user_dict)

            signals.user_sync.send(user.id)
            return user

        return self.create_oidc_user(userinfo)

    def oidc_info_into_plugin_extras(self, userinfo: dict[str, Any]) -> dict[str, Any]:
        return {"oidc_pkce": userinfo.copy()}

    def oidc_info_into_user_dict(self, userinfo: dict[str, Any]) -> dict[str, Any]:
        data = {
            "email": userinfo["email"],
            "name": _get_random_username_from_email(userinfo["email"]),
            "password": secrets.token_urlsafe(60),
            "fullname": userinfo["name"],
            "plugin_extras": self.oidc_info_into_plugin_extras(userinfo),
        }

        if config.same_id():
            data["id"] = userinfo["sub"]

        return data

    def create_oidc_user(self, userinfo: dict[str, Any]) -> model.User:
        user_dict = self.oidc_info_into_user_dict(userinfo)
        admin = tk.get_action("get_site_user")({"ignore_auth": True}, {})
        user = tk.get_action("user_create")({"user": admin["name"]}, user_dict)

        signals.user_create.send(user["id"])
        return model.User.get(user["id"])

    # def _attach_details(id: str, details):
    #     admin = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    #     user = tk.get_action("user_show")({"user": admin["name"]}, {"id": id, "include_plugin_extras": True})

    #     # do not drop extras that were set by other plugins
    #     extras = user.pop('plugin_extras', None) or {}
    #     patch = details.make_userdict()
    #     extras.update(patch['plugin_extras'])
    #     patch['plugin_extras'] = extras
    #     user.update(patch)

    #     # user_patch is not available in v2.9
    #     user = tk.get_action("user_update")({"user": admin["name"]}, user)
    #     return user
