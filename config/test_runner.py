"""Test runner that keeps uploaded test files out of the real media folder."""

import shutil
import tempfile

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class MrentalsTestRunner(DiscoverRunner):
    """Point MEDIA_ROOT at a throwaway directory for the duration of the run.

    Several models take image uploads, so without this every test run would
    litter the developer's media folder with fixtures.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._media_root = tempfile.mkdtemp(prefix="mrentals-test-media-")
        self._override = override_settings(MEDIA_ROOT=self._media_root)
        self._override.enable()

    def teardown_test_environment(self, **kwargs):
        self._override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)
        super().teardown_test_environment(**kwargs)
