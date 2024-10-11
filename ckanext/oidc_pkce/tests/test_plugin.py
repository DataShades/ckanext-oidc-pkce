# encoding: utf-8

from flask import redirect

from unittest.mock import MagicMock
import pytest

import ckan.plugins as p

from ckanext.oidc_pkce import plugin as plugin_module


class MockUser(object):
    """ Stub class to represent a logged-in user.
    """

    def __init__(self, name, oidc_enabled=False):
        """ Set up a stub name to return.
        """
        self.name = name
        self.is_authenticated = True if name else False
        if oidc_enabled:
            self.plugin_extras = {'oidc_pkce': {
                'sub': 1, 'name': name, 'email': 'test@localhost'
            }}


@pytest.mark.ckan_config("ckan.plugins", "oidc_pkce")
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert p.plugin_loaded("oidc_pkce")


if p.toolkit.check_ckan_version('2.10'):

    @pytest.mark.ckan_config("ckanext.oidc_pkce.base_url", "http://unit-test-sso")
    @pytest.mark.ckan_config("ckanext.oidc_pkce.logout_path", "/logout")
    def test_logout_flow():
        plugin_module.user_view.logout = MagicMock()
        plugin_module.user_view.logout.return_value = redirect("http://unit-test-ckan/logged_out")
        plugin_module.tk = MagicMock()
        plugin = plugin_module.OidcPkcePlugin()
        plugin_module.session = {}

        # no-op due to not being logged in
        plugin_module._current_user = lambda: MockUser(None)
        assert plugin.logout() is None
        plugin_module.user_view.logout.assert_not_called()

        # no-op due to not being SSO-enabled
        plugin_module._current_user = lambda: MockUser('test')
        assert plugin.logout() is None
        plugin_module.user_view.logout.assert_not_called()

        # no-op due to flag in session
        plugin_module.session['_in_logout'] = True
        plugin_module._current_user = lambda: MockUser('test', True)
        assert plugin.logout() is None
        plugin_module.user_view.logout.assert_not_called()
        assert plugin_module.session == {}

        # call core view and issue redirect
        result = plugin.logout()
        assert result.location == 'http://unit-test-sso/logout?redirect_uri=http://unit-test-ckan/logged_out'

    @pytest.mark.ckan_config("ckanext.oidc_pkce.base_url", "http://unit-test")
    def test_logout_disabled():
        plugin_module.user_view = MagicMock()
        plugin = plugin_module.OidcPkcePlugin()
        plugin_module._current_user = lambda: MockUser('test', True)

        # no-op due to config not having a logout path
        assert plugin.logout() is None
        plugin_module.user_view.logout.assert_not_called()
