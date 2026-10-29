import pytest

from ckan import model

from ckanext.oidc_pkce import utils
import ckan.plugins.toolkit as tk


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestSyncUser:
    def test_user_created(self, user_info):
        utils.sync_user(user_info)

        assert model.User.by_email(user_info["email"])

    def test_existing_user_attached(self, user_factory, user_info):
        user = user_factory(email=user_info["email"])
        utils.sync_user(user_info)

        attached = model.User.by_email(user_info["email"])
        if isinstance(attached, list):
            # CKAN < 2.10
            attached = attached[0]

        assert user["id"] == attached.id

    def test_sync_by_case_insensitive_email(self, user_factory, user_info):
        user = user_factory(email=user_info["email"].upper())
        utils.sync_user(user_info)

        attached = model.User.by_email(user_info["email"])
        if isinstance(attached, list):
            # CKAN < 2.10
            attached = attached[0]

        assert user["id"] == attached.id

    @pytest.mark.ckan_config("ckan.user.unique_email_states", ["active"])  # Needed to ensure compatibility in 2.12+
    def test_sync_ignores_deleted_users(self, user_factory, user_info):
        deleted_user = user_factory(
            email=user_info["email"],
            state="deleted",
        )
        active_user = user_factory(
            email=user_info["email"],
            state="active",
        )

        attached = utils.sync_user(user_info)

        assert attached.id == active_user["id"]
        assert attached.id != deleted_user["id"]

    @pytest.mark.ckan_config("ckan.user.unique_email_states", ["active"])  # Needed to ensure compatibility in 2.12+
    def test_2_12_sync_email_is_unique_with_no_active_email_found_new_user_created(self, user_factory, user_info):
        """Configuration to ignore deleted user and create new user account on SSO
        """
        deleted_user = user_factory(
            email=user_info["email"],
            state="deleted",
        )

        attached = utils.sync_user(user_info)

        assert attached.id != deleted_user["id"]

    @pytest.mark.skipif(not tk.check_ckan_version("2.12"), reason="This is for ckan 2.12+")
    @pytest.mark.ckan_config("ckan.user.unique_email_states", ["active", "deleted"])
    def test_2_12_sync_email_is_unique_with_unallowed_reused_email(self, user_factory, user_info):
        """Configuration can allow deleted user to be returned when configured to only have 1 unique email in db
        """

        deleted_user = user_factory(
            email=user_info["email"],
            state="deleted",
        )

        attached = utils.sync_user(user_info)

        assert attached.id == deleted_user["id"]

    @pytest.mark.skipif(not tk.check_ckan_version("2.12"), reason="This is for ckan 2.12+")
    def test_2_12_sync_email_is_not_unique_duplicate_found_error(self, user_factory, user_info):
        """Misconfiguration where deleted is included can return duplicates, so none are returned
        """

        user_factory(
            email=user_info["email"],
            state="deleted",
        )
        user_factory(
            email=user_info["email"],
            state="active",
        )

        # Make both now be included i.e. for long lived systems and requirement changes
        tk.config["ckan.user.unique_email_states"] = ["active", "deleted"]

        attached = utils.sync_user(user_info)

        assert attached is None

    @pytest.mark.ckan_config("ckan.user.unique_email_states", ["active"])
    def test_get_oidc_user_matches_by_sub_with_changed_email(self, user_factory):
        """Test to correctly finds a user using the 'sub' stored in plugin_extras, even if the email has changed.
        """

        user_info = {
            "email": "original@abc.com",
            "name": "Original User",
            "sub": "111Sub"
        }

        # Manually create user to ensure plugin_extras is set correctly
        user = user_factory(
            email=user_info["email"],
            plugin_extras={"oidc_pkce": {"sub": user_info["sub"]}}
        )
        # user.plugin_extras = {"oidc_pkce": {"sub": user_info["sub"]}}
        # model.Session.instance().add(user)
        # model.Session.instance().commit()

        # This simulates a user changing their email in the Identity Provider or on site
        new_user_info = {
            "sub": "111Sub",
            "email": "new_email@abcefg.com",
            "name": "New Email User",
        }

        matched_user = utils.sync_user(new_user_info)

        assert matched_user is not None
        assert matched_user.id == user.get("id")
        assert matched_user.email == user_info["email"]

    def test_get_oidc_user_ignores_inactive_users_for_sub_on_signup(self, user_factory):
        """verify a user with a matching 'sub' but 'deleted' state is NOT returned
        """
        sub_value = "deleted_sub_999"

        # Create a deleted user with the matching sub
        deleted_user = user_factory(
            email="deleted@abc.com",
            state="deleted",
            plugin_extras={"oidc_pkce": {"sub": sub_value}}
        )
        # deleted_user.plugin_extras = {"oidc_pkce": {"sub": sub_value}}
        # model.Session.instance().add(deleted_user)
        # model.Session.instance().commit()

        user_info = {
            "sub": sub_value,
            "email": "deleted@abc.com",
            "name": "Deleted User",
        }

        matched_user = utils.sync_user(user_info)

        assert matched_user is not None
        assert matched_user.id != deleted_user["id"]
