import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from fastapi import HTTPException
from app.services import auth_service as auth


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        directory = Path(self.temp.name)
        self.patches = [patch.object(auth, 'USERS_DB', directory / 'users.db'),
                        patch.object(auth, 'USERS_FILE', directory / 'users.json'),
                        patch.object(auth, '_DB_INITIALIZED', False)]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_new_install_requires_explicit_password(self):
        with patch.dict(os.environ, {'ROCKBURST_ADMIN_PASSWORD': ''}):
            with self.assertRaises(HTTPException) as result:
                auth._ensure_store()
            self.assertEqual(result.exception.status_code, 503)

    def test_only_admin_created_and_existing_password_preserved(self):
        import secrets
        password = secrets.token_urlsafe(24)
        with patch.dict(os.environ, {'ROCKBURST_ADMIN_PASSWORD': password}):
            auth._ensure_store()
            self.assertEqual([u['username'] for u in auth._load_users()], ['admin'])
            self.assertEqual(auth.authenticate('admin', password)['username'], 'admin')
        auth._DB_INITIALIZED = False
        with patch.dict(os.environ, {'ROCKBURST_ADMIN_PASSWORD': ''}):
            self.assertEqual(auth.authenticate('admin', password)['username'], 'admin')


if __name__ == '__main__':
    unittest.main()
