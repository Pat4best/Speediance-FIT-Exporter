import struct
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from fitwriter import crc, write_fit


class Tests(unittest.TestCase):
    def test_fit_integrity(self):
        workout = {
            "day": "2026-11-13", "title": "Test",
            "finished_at": "2026-11-13 19:10:00",
            "duration_min": 8, "calories": 45, "unit": "kg",
            "exercises": [{"name": "Kreuzheben",
                           "sets": [{"reps": 5, "weight": 35, "seconds": 30}]}],
        }
        with TemporaryDirectory() as folder:
            data = write_fit(workout, Path(folder) / "test.fit").read_bytes()
            self.assertEqual(data[8:12], b".FIT")
            self.assertEqual(struct.unpack("<H", data[-2:])[0], crc(data[:-2]))
            self.assertEqual(struct.unpack("<I", data[4:8])[0], len(data) - 16)
            self.assertGreater(len(data), 120)


if __name__ == "__main__":
    unittest.main()
