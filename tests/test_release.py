import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))

from fastapi import HTTPException, UploadFile
from app.services.surfer_service import SurferService
from app.core.config import settings
from scripts.package_release import included


class ReleaseTests(unittest.TestCase):
    def test_package_excludes_local_files(self):
        for name in ['docs/notes.md', 'server/data/users.db', 'server/config/users.json',
                     'server/config/app_config.json', 'database/model.blend', '.env',
                     'server/output/map.png', 'server/__pycache__/main.pyc']:
            self.assertFalse(included(ROOT / name), name)
        for name in ['database/centerline_points.csv', 'public/models/hangdao.glb',
                     'server/config/app_config.example.json', 'src/assets/font/D-DIN-Bold.otf',
                     'public/samples/hongyang-warning-demo.xls', 'README.md']:
            self.assertTrue(included(ROOT / name), name)

    def test_demo_assets_are_complete(self):
        from app.services.microseismic_service import microseismic_service
        sample = ROOT / 'public/samples/hongyang-warning-demo.xls'
        rows = microseismic_service.build_surfer_rows(sample.read_bytes())
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(
            {p.name for p in (ROOT / 'public/models').glob('*.glb')},
            {'hangdao.glb', 'hongyang-coal12-georef.glb'},
        )
        for name in ['hongyang-coal12-georef.json', 'hongyang-microseismic-events.json',
                     'hongyang-rockburst-warning-map.png']:
            self.assertTrue((ROOT / 'public/defaults' / name).is_file(), name)

    def generate_failure(self, contents, expected, busy=False, too_large=False):
        service = SurferService()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(settings, 'upload_folder', Path(folder)), \
                 patch.object(settings, 'output_folder', Path(folder)), \
                 patch.object(settings, 'max_upload_mb', 0 if too_large else 30):
                if busy:
                    service._lock.acquire()
                try:
                    with self.assertRaises(HTTPException) as error:
                        service.generate(UploadFile(filename='../unsafe.xls', file=io.BytesIO(contents)))
                    self.assertEqual(error.exception.status_code, expected)
                    self.assertEqual(list(Path(folder).iterdir()), [])
                finally:
                    if busy:
                        service._lock.release()
                self.assertTrue(service._lock.acquire(blocking=False))
                service._lock.release()

    def test_empty_upload_cleanup(self):
        self.generate_failure(b'', 400)

    def test_invalid_workbook_cleanup(self):
        self.generate_failure(b'not excel', 400)

    def test_busy_upload_cleanup(self):
        self.generate_failure(b'data', 409, busy=True)

    def test_oversize_upload_cleanup(self):
        self.generate_failure(b'data', 413, too_large=True)


if __name__ == '__main__':
    unittest.main()
