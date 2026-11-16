"""Independent wire-format regression checks for Garmin FIT activity files."""
import struct
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from fitwriter import write_fit, crc

SIZES = {0: ("B", 1), 2: ("B", 1), 0x84: ("H", 2), 0x86: ("I", 4), 0x8C: ("I", 4)}


def decode(data):
    """Strictly decode every message (catches missing architecture byte)."""
    assert data[8:12] == b".FIT"
    assert crc(data[:12]) == struct.unpack_from("<H", data, 12)[0]
    assert crc(data[:-2]) == struct.unpack_from("<H", data, len(data) - 2)[0]
    assert len(data) == 16 + struct.unpack_from("<I", data, 4)[0]
    pos = 14
    defs, messages = {}, []
    while pos < len(data) - 2:
        head = data[pos]
        pos += 1
        assert not head & 128, "Compressed timestamps not used"
        local = head & 15
        if head & 64:
            reserved, architecture, global_num, count = struct.unpack_from("<BBHB", data, pos)
            pos += 5
            assert (reserved, architecture) == (0, 0)
            fields = []
            for _ in range(count):
                field, width, kind = struct.unpack_from("<BBB", data, pos)
                pos += 3
                assert (kind == 7 and 0 < width <= 255) or (kind in SIZES and SIZES[kind][1] == width)
                fields.append((field, kind, width))
            defs[local] = (global_num, fields)
        else:
            assert local in defs, "Missing FIT definition"
            num, fields = defs[local]
            values = {}
            for field, kind, width in fields:
                if kind == 7:
                    value = data[pos:pos + width].split(bytes([0]), 1)[0].decode("utf-8")
                else:
                    fmt, _ = SIZES[kind]
                    value = struct.unpack_from("<" + fmt, data, pos)[0]
                values[field] = (kind, value)
                pos += width
            messages.append((num, values))
    assert pos == len(data) - 2
    return messages


class ProfileTest(unittest.TestCase):
    def build(self, dest, unit="kg", weight=35):
        return write_fit({
            "training_id": 1189260, "day": "2026-11-13",
            "finished_at": "2026-11-13T19:20:00", "duration_min": 10,
            "calories": 60, "unit": unit,
            "exercises": [{"name": "Kreuzheben", "sets": [
                {"reps": 5, "weight": weight, "seconds": 30},
                {"reps": 8, "weight": weight, "seconds": 20},
            ]}],
        }, dest)

    def test_required_activity_and_correct_sport(self):
        with TemporaryDirectory() as folder:
            ms = decode(self.build(Path(folder) / "a.fit").read_bytes())
            numbers = [num for num, _ in ms]
            self.assertEqual(numbers[0], 0)
            self.assertEqual(numbers.count(18), 1)
            self.assertEqual(numbers.count(19), 1)
            self.assertEqual(numbers.count(34), 1)
            self.assertGreaterEqual(numbers.count(20), 2)
            self.assertEqual(numbers.count(225), 2)
            file_id = ms[0][1]
            self.assertEqual(file_id[0], (0, 4))
            self.assertEqual(file_id[1], (0x84, 255))
            self.assertNotEqual(file_id[4][1], 0)
            session = next(fields for n, fields in ms if n == 18)
            self.assertEqual(session[5], (0, 10))   # training, not swim
            self.assertEqual(session[6], (0, 20))   # strength training
            act = next(fields for n, fields in ms if n == 34)
            self.assertEqual(act[1], (0x84, 1))
            self.assertEqual(act[4], (0, 1))

    def test_correct_set_layout_and_weight_scale(self):
        with TemporaryDirectory() as folder:
            ms = decode(self.build(Path(folder) / "b.fit").read_bytes())
            sets = [f for n, f in ms if n == 225]
            self.assertEqual(sets[0][3], (0x84, 5))      # reps
            self.assertEqual(sets[0][4], (0x84, 560))    # 35 kg * 16
            self.assertEqual(sets[0][5], (2, 1))        # active
            self.assertEqual(sets[0][0], (0x86, 30000))  # duration
            self.assertEqual(sets[0][254][1] - sets[0][6][1], 30)

    def test_set_exercise_category_and_subtype(self):
        with TemporaryDirectory() as folder:
            ms = decode(self.build(Path(folder) / "e.fit").read_bytes())
            sets = [f for n, f in ms if n == 225]
            self.assertEqual(len(sets), 2)
            self.assertTrue(all(f[7] == (0x84, 8) for f in sets))
            self.assertTrue(all(f[8] == (0x84, 0) for f in sets))

    def test_unknown_names_are_not_bench_press(self):
        with TemporaryDirectory() as folder:
            p = write_fit({
                "day": "2026-11-13", "duration_min": 5,
                "exercises": [
                    {"name": "Hohe Knie", "sets": [{"seconds": 30}]},
                    {"name": "Skater", "sets": [{"seconds": 25}]},
                    {"name": "Sternsprünge", "sets": [{"seconds": 30}]},
                ]
            }, Path(folder) / "warmup.fit")
            ms = decode(p.read_bytes())
            sets = [f for n, f in ms if n == 225]
            self.assertEqual([(f[7][1], f[8][1]) for f in sets],
                             [(65534, 0), (65534, 1), (2, 12)])
            titles = [f for n, f in ms if n == 264]
            self.assertEqual([f[2][1] for f in titles], ["Hohe Knie", "Skater"])

    def test_pounds_to_kg(self):
        with TemporaryDirectory() as folder:
            ms = decode(self.build(Path(folder) / "c.fit", "lb", 100).read_bytes())
            strength = next(f for n, f in ms if n == 225)
            self.assertAlmostEqual(strength[4][1] / 16, 45.36, delta=0.05)

    def test_empty_detail_still_has_activity_records(self):
        with TemporaryDirectory() as folder:
            p = write_fit({"day": "2026-11-13", "duration_min": 5,
                           "exercises": []}, Path(folder) / "d.fit")
            numbers = [n for n, _ in decode(p.read_bytes())]
            self.assertEqual(numbers.count(225), 0)
            self.assertEqual(numbers.count(20), 2)


if __name__ == "__main__":
    unittest.main()
