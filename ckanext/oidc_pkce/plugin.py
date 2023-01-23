from __future__ import annotations

from typing import Optional, Any

from flask.wrappers import Response

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import session

if tk.check_ckan_version("2.10"):
    from ckan.common import login_user
from . import views, interfaces, utils, helpers


class OidcPkcePlugin(p.SingletonPlugin):
    p.implements(p.IAuthenticator, inherit=True)
    p.implements(p.IBlueprint)
    p.implements(p.ITemplateHelpers)
    p.implements(interfaces.IOidcPkce, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # IAuthenticator
    def identify(self) -> Optional[Response]:
        user = model.User.get(session.get(utils.SESSION_USER))

        if user:
            # CKAN < 2.10
            tk.g.user = user.name
            tk.g.userobj = user
            if tk.check_ckan_version("2.10"):
                login_user(user)

    def logout(self):
        utils.logout()

    # ITemplateHelpers
    def get_helpers(
        self,
    ):
        return helpers.get_helpers()
