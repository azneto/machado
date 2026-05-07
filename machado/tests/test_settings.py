from django.test import TestCase, override_settings
from machado import settings as machado_settings
import sys
from types import ModuleType


class SettingsTest(TestCase):
    def test_patch_root_urlconf_hasattr(self):
        # Create a dummy module
        dummy_urlconf = ModuleType("dummy_urlconf")
        dummy_urlconf.urlpatterns = []
        sys.modules["dummy_urlconf"] = dummy_urlconf

        with override_settings(ROOT_URLCONF="dummy_urlconf"):
            machado_settings.patch_root_urlconf()
            # It should have appended the machado urlpatterns to the dummy_urlconf
            from machado.urls import urlpatterns

            self.assertEqual(dummy_urlconf.urlpatterns, urlpatterns)

    def test_patch_templates_empty(self):
        with override_settings(TEMPLATES=[]):
            machado_settings.patch_templates()
            from django.conf import settings

            self.assertEqual(len(settings.TEMPLATES), 1)
            self.assertEqual(
                settings.TEMPLATES[0]["BACKEND"],
                "django.template.backends.django.DjangoTemplates",
            )

    def test_patch_templates_not_empty(self):
        # Tests the branch where len(settings.TEMPLATES) != 0
        with override_settings(TEMPLATES=[{}]):
            machado_settings.patch_templates()
            from django.conf import settings

            self.assertEqual(len(settings.TEMPLATES), 1)
