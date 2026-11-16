"""Minimal Garmin FIT activity writer, standard-library only.

Emits file_id, event, strength set, session, lap and activity messages.
Does not invent heart rate or GPS data. Missing set timestamps are estimates.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import struct

FIT_EPOCH = datetime(1989, 12, 31, tzinfo=timezone.utc)
FORMATS = {0: "B", 1: "b", 2: "B", 0x84: "H", 0x86: "I", 0x88: "f"}


def stamp(value):
    if value.tzinfo is None:
        value = value.astimezone()
    return max(0, int((value.astimezone(timezone.utc) - FIT_EPOCH).total_seconds()))


def crc(data):
    table = (
        0x0, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
    )
    value = 0
    for byte in data:
        t = table[value & 15]
        value = ((value >> 4) & 0x0FFF) ^ t ^ table[byte & 15]
        t = table[value & 15]
        value = ((value >> 4) & 0x0FFF) ^ t ^ table[(byte >> 4) & 15]
    return value


class Encoder:
    def __init__(self):
        self.buf = bytearray()
        self.local = 0

    def mesg(self, global_num, fields):
        loc = self.local % 16
        self.local += 1
        self.buf.extend(bytes([0x40 | loc, 0]) + struct.pack("<H", global_num) + bytes([len(fields)]))
        for number, typ, _ in fields:
            self.buf.extend(bytes([number, struct.calcsize("<" + FORMATS[typ]), typ]))
        self.buf.append(loc)
        for _, typ, value in fields:
            self.buf.extend(struct.pack("<" + FORMATS[typ], value))

    def result(self):
        header = struct.pack("<BBHI4s", 14, 0x20, 0x0100, len(self.buf), b".FIT")
        header += struct.pack("<H", crc(header))
        data = header + self.buf
        return data + struct.pack("<H", crc(data))


def write_fit(workout, destination):
    finished = workout.get("finished_at")
    day = workout["day"]
    if finished:
        try:
            end = datetime.fromisoformat(str(finished).replace("Z", "+00:00"))
        except ValueError:
            end = datetime.fromisoformat(day + "T12:00:00")
    else:
        end = datetime.fromisoformat(day + "T12:00:00")

    all_sets = [s for ex in workout.get("exercises", []) for s in ex.get("sets", [])]
    set_seconds = sum(max(0, int(s.get("seconds") or 0)) for s in all_sets)
    duration = max(60, int(float(workout.get("duration_min") or 0) * 60))
    if not workout.get("duration_min") and set_seconds:
        duration = max(60, set_seconds)
    start = end - timedelta(seconds=duration) if finished else end
    start_ts = stamp(start)
    end_ts = stamp(start + timedelta(seconds=duration))
    duration_ms = min(0xFFFFFFFF, duration * 1000)
    enc = Encoder()

    enc.mesg(0, [(0, 0, 4), (1, 0x84, 1), (2, 0x84, 0), (3, 0x86, start_ts), (4, 0x86, 0)])
    enc.mesg(21, [(253, 0x86, start_ts), (0, 0, 0), (1, 0, 0)])
    remaining = duration
    cursor = start
    unit_factor = 0.45359237 if workout.get("unit") == "lb" else 1.0

    for i, item in enumerate(all_sets):
        provided = int(item.get("seconds") or 0)
        seconds = min(max(1, provided), max(1, remaining)) if provided > 0 else min(
            30, max(1, remaining // max(1, len(all_sets) - i))
        )
        fields = [
            (254, 0x86, stamp(cursor)),
            (0, 0x86, seconds * 1000),
            (3, 0x84, max(0, min(65535, int(item.get("reps") or 0)))),
            (5, 0x88, round(float(item.get("weight") or 0) * unit_factor, 3)),
            (6, 0, 1),
        ]
        enc.mesg(225, fields)
        cursor += timedelta(seconds=seconds)
        remaining = max(0, remaining - seconds)

    enc.mesg(21, [(253, 0x86, end_ts), (0, 0, 0), (1, 0, 1)])
    enc.mesg(18, [
        (253, 0x86, end_ts), (2, 0x86, start_ts),
        (5, 0, 5), (6, 0, 20), (7, 0x86, duration_ms), (8, 0x86, duration_ms),
        (9, 0x86, 0), (11, 0x84, min(65535, max(0, int(workout.get("calories") or 0)))),
        (25, 0x84, 0), (26, 0x84, 1),
    ])
    enc.mesg(19, [
        (253, 0x86, end_ts), (2, 0x86, start_ts),
        (7, 0x86, duration_ms), (8, 0x86, duration_ms),
        (9, 0x86, 0), (25, 0, 0),
    ])
    enc.mesg(34, [(253, 0x86, end_ts), (0, 0x86, duration_ms), (1, 0x84, 1), (2, 0, 0), (3, 0, 26)])
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(enc.result())
    return path
