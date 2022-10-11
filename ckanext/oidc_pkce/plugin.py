from __future__ import annotations

from typing import Optional, Any

from flask.wrappers import Response

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import session

from . import views, interfaces, utils

try:
    from ckan.common import login_user
except ImportError:
    login_user = lambda _: ...


class OidcPkcePlugin(p.SingletonPlugin):
    p.implements(p.IAuthenticator, inherit=True)
    p.implements(p.IBlueprint)
    p.implements(interfaces.IOidcPkce, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # IAuthenticator
    def identify(self) -> Optional[Response]:
        user = model.User.get(session.get(utils.SESSION_USER))

        if user:
            tk.g.user = user.name
            tk.g.userobj = user
            login_user(user)

    def logout(self):
        utils.logout()
