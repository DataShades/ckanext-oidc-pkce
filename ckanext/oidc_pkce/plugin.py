from __future__ import annotations

import logging
from typing import Optional

from flask import redirect
from flask.wrappers import Response

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import session
from ckan.views import user as user_view

from . import config, helpers, interfaces, utils, views

log = logging.getLogger(__name__)

try:
    config_declarations = tk.blanket.config_declarations
except AttributeError:
    def config_declarations(cls):
        return cls


def _current_user():
    if tk.check_ckan_version('2.10'):
        from ckan.common import current_user
        return current_user
    return tk.g.userobj


@config_declarations
class OidcPkcePlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IAuthenticator, inherit=True)
    p.implements(interfaces.IOidcPkce, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')

    # ITemplateHelpers
    def get_helpers(
        self,
    ):
        return helpers.get_helpers()

    # IAuthenticator

    if tk.check_ckan_version("2.10"):

        def logout(self):
            """ We want to return a view after the regular logout logic,
            rather than before.

            We set a flag to indicate that we're in the middle of logout,
            then call the regular logout view. The view calls a second
            instance of this function, which detects the flag and no-ops,
            allowing the view to proceed and wipe the session.

            After it completes, we assemble a redirect and pass that back
            to the code that originally called this function.
            """
            if session.pop("_in_logout", False):
                log.debug("SSO logout found in-progress flag, skipping recursive call")
                return None
            current_user = _current_user()
            if not current_user.is_authenticated:
                log.info("No current user found, skipping SSO logout")
                return None
            plugin_extras = getattr(current_user, 'plugin_extras', None)
            if not plugin_extras or not plugin_extras.get('oidc_pkce'):
                log.info("Current user [%s] is not associated with SSO, skipping SSO logout",
                         current_user.name)
                return None

            log.info("Logging out [%s]", current_user.name)
            sso_logout_url = config.logout_url()
            if not sso_logout_url:
                log.info("No SSO logout path configured, logout of [%s] will be local only",
                         current_user.name)
                return None
            session["_in_logout"] = True
            original_response = user_view.logout()
            log.debug("Redirecting [%s] to SSO logout: %s", current_user.name, sso_logout_url)
            return redirect(sso_logout_url + '?redirect_uri=' + original_response.location)
    else:
        def identify(self) -> Optional[Response]:
            user = model.User.get(session.get(utils.SESSION_USER))
            if user:
                tk.g.user = user.name
                tk.g.userobj = user

        def logout(self):
            session.pop(utils.SESSION_USER, None)
