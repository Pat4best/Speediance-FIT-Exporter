"""Read only measured metrics from a real Garmin FIT activity.

The original Garmin file is never rewritten. FIT reader consumes developer
fields and compressed timestamp headers but only exports recognized training
metrics. We do not claim Garmin hardware metadata for newly generated FITs.
"""
from datetime import datetime, timedelta, timezone
import struct

from fitwriter import FIT_EPOCH, crc


class GarminFitError(ValueError):
    pass


_BASE_FORMATS = {
    0: ("B", 1), 1: ("b", 1), 2: ("B", 1), 3: ("h", 2),
    4: ("H", 2), 5: ("i", 4), 6: ("I", 4),
    8: ("f", 4), 9: ("d", 8), 10: ("B", 1),
    11: ("H", 2), 12: ("I", 4), 14: ("q", 8),
    15: ("Q", 8), 16: ("Q", 8),
}


def _decoded_scalar(data, base_type, endian):
    type_id = base_type & 0x1F
    if type_id not in _BASE_FORMATS:
        return None
    fmt, size = _BASE_FORMATS[type_id]
    if len(data) < size:
        return None
    val = struct.unpack(endian + fmt, data[:size])[0]
    # FIT invalid sentinels, including zero-invalid types.
    if type_id in (10, 11, 12, 16) and val == 0:
        return None
    invalid = {
        0: 255, 1: 127, 2: 255, 3: 32767, 4: 65535,
        5: 2147483647, 6: 4294967295, 14: 9223372036854775807,
        15: 18446744073709551615,
    }
    if val == invalid.get(type_id):
        return None
    return val


def read_garmin_activity(fit_bytes):
    """Extract HR records (absolute datetime), session HR, kcal and timing."""
    if not isinstance(fit_bytes, bytes) or len(fit_bytes) < 16:
        raise GarminFitError("Ungültige FIT-Datei")
    header_size = fit_bytes[0]
    if header_size not in (12, 14) or fit_bytes[8:12] != b".FIT":
        raise GarminFitError("Garmin-Aktivität hat keinen gültigen FIT-Header")
    data_size = struct.unpack_from("<I", fit_bytes, 4)[0]
    end = header_size + data_size
    if end + 2 != len(fit_bytes) or data_size > 24 * 1024 * 1024:
        raise GarminFitError("FIT-Länge ist ungültig")
    if header_size == 14 and crc(fit_bytes[:12]) != struct.unpack_from("<H", fit_bytes, 12)[0]:
        raise GarminFitError("FIT-Header-Prüfsumme fehlerhaft")
    if crc(fit_bytes[:-2]) != struct.unpack_from("<H", fit_bytes, end)[0]:
        raise GarminFitError("FIT-Datei-Prüfsumme fehlerhaft")

    p = header_size
    definitions = {}
    last_timestamps = {}
    records = {}
    session = {}
    while p < end:
        h = fit_bytes[p]
        p += 1
        is_compressed = bool(h & 0x80)
        local = (h >> 5) & 3 if is_compressed else h & 15
        if not is_compressed and h & 0x40:
            if p + 5 > end:
                raise GarminFitError("FIT-Definition abgeschnitten")
            _reserved, arch = fit_bytes[p], fit_bytes[p + 1]
            if arch not in (0, 1):
                raise GarminFitError("Unbekannte FIT-Bytefolge")
            endian = "<" if arch == 0 else ">"
            message_type = struct.unpack_from(endian + "H", fit_bytes, p + 2)[0]
            count = fit_bytes[p + 4]
            p += 5
            if p + 3 * count > end:
                raise GarminFitError("FIT-Felder abgeschnitten")
            fields = []
            for _ in range(count):
                fields.append(tuple(fit_bytes[p:p + 3]))
                p += 3
            dev_fields = []
            if h & 0x20:
                if p + 1 > end:
                    raise GarminFitError("FIT-Entwicklerfelder abgeschnitten")
                dev_count = fit_bytes[p]
                p += 1
                if p + dev_count * 3 > end:
                    raise GarminFitError("FIT-Entwicklerfelder abgeschnitten")
                for _ in range(dev_count):
                    dev_fields.append(tuple(fit_bytes[p:p + 3]))
                    p += 3
            definitions[local] = (message_type, endian, fields, dev_fields)
            continue
        if local not in definitions:
            raise GarminFitError("Unbekannte FIT-Nachrichtendefinition")
        message_type, endian, fields, dev_fields = definitions[local]
        values = {}
        for field_number, width, base_type in fields:
            if p + width > end:
                raise GarminFitError("FIT-Daten abgeschnitten")
            if ((message_type == 20 and field_number in (253, 3))
                    or (message_type == 18 and field_number in (2, 7, 8, 11, 16, 17))):
                values[field_number] = _decoded_scalar(fit_bytes[p:p + width], base_type, endian)
            p += width
        for _number, width, _type in dev_fields:
            if p + width > end:
                raise GarminFitError("FIT-Entwicklerdaten abgeschnitten")
            p += width
        if is_compressed:
            offset = h & 0x1F
            previous = last_timestamps.get(local)
            if previous is not None:
                ts = (previous & ~31) + offset
                if ts < previous:
                    ts += 32
                if values.get(253) is None:
                    values[253] = ts
        if values.get(253) is not None:
            last_timestamps[local] = int(values[253])
        if message_type == 20:
            ts = values.get(253)
            hr = values.get(3)
            if ts is not None and hr is not None and 20 <= hr <= 254:
                records[int(ts)] = int(hr)
        if message_type == 18:
            session = values

    def fit_datetime(seconds):
        if seconds is None:
            return None
        return FIT_EPOCH + timedelta(seconds=int(seconds))
    start = fit_datetime(session.get(2))
    if start is None and records:
        start = fit_datetime(min(records))
    elapsed_ms = session.get(7) or session.get(8)
    duration = (float(elapsed_ms) / 1000 if elapsed_ms is not None and elapsed_ms > 0
                else None)
    return {
        "start": start,
        "duration_seconds": duration,
        "heart_rate_records": [(fit_datetime(ts), bpm) for ts, bpm in sorted(records.items())],
        "heart_rate_summary": {"avg": session.get(16), "max": session.get(17)},
        "calories": session.get(11),
        "record_count": len(records),
    }
