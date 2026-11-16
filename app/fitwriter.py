"""Minimal Garmin FIT activity writer, standard-library only.

Emits file_id, event, strength set, session, lap and activity messages.
Does not invent heart rate or GPS data. Missing set timestamps are estimates.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import struct

FIT_EPOCH = datetime(1989, 12, 31, tzinfo=timezone.utc)
FORMATS = {0: "B", 2: "B", 0x84: "H", 0x86: "I", 0x8C: "I"}


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
        self.buf.extend(bytes([0x40 | loc, 0, 0]) + struct.pack("<H", global_num) + bytes([len(fields)]))
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
    """Create Garmin FIT *activity* (strength training), not a workout plan.

    FIT field numbers/scaling follow Garmin FIT Profile: the original exporter
    had a missing architecture byte, wrong sport type and malformed set fields.
    No GPS, heart-rate or cadence readings are made up.
    """
    day = workout["day"]
    finished = workout.get("finished_at")
    try:
        end = datetime.fromisoformat(str(finished).replace("Z", "+00:00")) if finished else None
    except ValueError:
        end = None

    sets = [s for ex in workout.get("exercises", []) for s in ex.get("sets", [])]
    measured_seconds = sum(max(0, int(float(s.get("seconds") or 0))) for s in sets)
    configured_seconds = int(float(workout.get("duration_min") or 0) * 60)
    duration = max(60, configured_seconds, measured_seconds, len(sets))
    start = end - timedelta(seconds=duration) if end else datetime.fromisoformat(day + "T12:00:00")
    start_ts = stamp(start)
    end_ts = stamp(start + timedelta(seconds=duration))
    duration_ms = duration * 1000
    calories = max(0, min(65534, int(float(workout.get("calories") or 0))))
    serial = int(workout.get("training_id") or 1) & 0xFFFFFFFF or 1
    unit_factor = 0.45359237 if workout.get("unit") == "lb" else 1.0
    enc = Encoder()

    # File ID: type ACTIVITY=4; manufacturer DEVELOPMENT=255, not Garmin.
    enc.mesg(0, [(0, 0, 4), (1, 0x84, 255), (2, 0x84, 0),
                 (3, 0x8C, serial), (4, 0x86, start_ts)])
    # Event TIMER=0, event_type START=0.
    enc.mesg(21, [(253, 0x86, start_ts), (0, 0, 0), (1, 0, 0)])
    # FIT Activity files expect Record messages, including timestamp and data.
    # Strength sessions are stationary; distance is always 0 m, no fake HR.
    enc.mesg(20, [(253, 0x86, start_ts), (5, 0x86, 0)])

    cursor = start
    remaining = duration
    for i, s in enumerate(sets):
        provided = max(0, int(float(s.get("seconds") or 0)))
        budget = max(1, remaining - (len(sets) - i - 1))
        seconds = max(1, min(budget, provided if provided else 30))
        set_start = stamp(cursor)
        cursor += timedelta(seconds=seconds)
        remaining = max(0, remaining - seconds)
        repetitions = max(0, min(65534, int(float(s.get("reps") or 0))))
        weight_kg = max(0, float(s.get("weight") or 0) * unit_factor)
        weight_scaled = min(65534, round(weight_kg * 16))
        enc.mesg(225, [
            (254, 0x86, stamp(cursor)),       # SET timestamp (unlike other messages)
            (0, 0x86, seconds * 1000),        # SET duration; FIT scale 1000
            (3, 0x84, repetitions),
            (4, 0x84, weight_scaled),         # weight; FIT scale 16 kg
            (5, 2, 1),                       # set_type ACTIVE
            (6, 0x86, set_start),
            (7, 0x84, 0),                    # exercise category UNKNOWN
        ])

    enc.mesg(20, [(253, 0x86, end_ts), (5, 0x86, 0)])
    enc.mesg(21, [(253, 0x86, end_ts), (0, 0, 0), (1, 0, 4)])  # STOP_ALL
    enc.mesg(19, [
        (254, 0x84, 0), (253, 0x86, end_ts), (0, 0, 9), (1, 0, 1),
        (2, 0x86, start_ts), (7, 0x86, duration_ms),
        (8, 0x86, duration_ms), (9, 0x86, 0),
        (25, 0, 10), (39, 0, 20),
    ])
    # Sport TRAINING=10; sub_sport STRENGTH_TRAINING=20 (not swimming=5).
    enc.mesg(18, [
        (254, 0x84, 0), (253, 0x86, end_ts), (0, 0, 8), (1, 0, 1),
        (2, 0x86, start_ts), (5, 0, 10), (6, 0, 20),
        (7, 0x86, duration_ms), (8, 0x86, duration_ms),
        (9, 0x86, 0), (11, 0x84, calories),
        (25, 0x84, 0), (26, 0x84, 1),
    ])
    enc.mesg(34, [
        (253, 0x86, end_ts), (0, 0x86, duration_ms), (1, 0x84, 1),
        (2, 0, 0), (3, 0, 26), (4, 0, 1),
    ])
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(enc.result())
    return path
