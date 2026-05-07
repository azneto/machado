from django.test import TestCase
from django.apps import apps
from unittest.mock import patch
from django.db.utils import ProgrammingError
import warnings

from machado.apps import MachadoConfig


class AppsTest(TestCase):
    def test_apps_ready_success(self):
        # Already executed during django setup, but we can call it again
        config = apps.get_app_config("machado")
        with patch("machado.settings.patch_all") as mock_patch:
            config.ready()
            mock_patch.assert_called_once()

    def test_apps_ready_programming_error_cvterm(self):
        config = apps.get_app_config("machado")
        with patch("machado.settings.patch_all", side_effect=ProgrammingError('relation "cvterm" does not exist')):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config.ready()
                self.assertEqual(len(w), 1)
                self.assertIn("You need to run: 'python manage.py migrate'", str(w[-1].message))

    def test_apps_ready_programming_error_other(self):
        config = apps.get_app_config("machado")
        with patch("machado.settings.patch_all", side_effect=ProgrammingError('some other error')):
            # It should just pass
            config.ready()
