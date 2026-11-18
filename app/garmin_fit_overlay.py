"""Non-destructive Garmin-FIT-first overlay for Speediance strength training.

Copy original Garmin FIT messages byte-for-byte, except selected numeric
summary/HR fields and the old Garmin strength SET messages (replaced by the
recorded Speediance sets). Preserve all Garmin device_info, developer fields,
proprietary messages, cadence, native motion samples and timestamps. New
Speediance data is inserted with temporary FIT local-message definitions;
the previously active definition is restored before returning to Garmin data.

No changes are made to any Garmin Connect activity or the downloaded file.
"""
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from secrets import randbits
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import logging

from fitwriter import crc, stamp, write_fit
from garmin_fit_reader import GarminFitError, _decoded_scalar
from garmin_merge import merge_workout, check_priorities


class GarminOverlayError(ValueError):
    pass


def parse_fit_wire(source):
    """Read raw FIT messages, including nonstandard/developer fields.

    Preserve raw bytes and the original field definitions for re-emission.
    This is not a lossy generic FIT-decoder/re-encoder.
    """
    if not isinstance(source, bytes) or len(source) < 16:
        raise GarminOverlayError("Ungültige Garmin-FIT-Datei")
    hs = source[0]
    if hs not in (12, 14) or source[8:12] != b".FIT":
        raise GarminOverlayError("FIT-Datei ohne gültige Signatur")
    data_size = struct.unpack_from("<I", source, 4)[0]
    end = hs + data_size
    if end + 2 != len(source) or data_size > 24 * 1024 * 1024:
        raise GarminOverlayError("Unplausible FIT-Dateigröße")
    if hs == 14 and crc(source[:12]) != struct.unpack_from("<H", source, 12)[0]:
        raise GarminOverlayError("FIT-Header-Prüfsumme nicht korrekt")
    if crc(source[:end]) != struct.unpack_from("<H", source, end)[0]:
        raise GarminOverlayError("FIT-Daten-Prüfsumme nicht korrekt")
    pos = hs
    active = {}
    last_times = {}
    chunks = []
    while pos < end:
        begin = pos
        header = source[pos]
        pos += 1
        compressed = bool(header & 0x80)
        local = ((header >> 5) & 3) if compressed else (header & 15)
        if not compressed and header & 0x40:
            if pos + 5 > end:
                raise GarminOverlayError("Unvollständige FIT-Definition")
            arch = source[pos + 1]
            if arch not in (0, 1):
                raise GarminOverlayError("Ungültige FIT-Architektur")
            endian = "<" if arch == 0 else ">"
            global_num = struct.unpack_from(endian + "H", source, pos + 2)[0]
            count = source[pos + 4]
            pos += 5
            if pos + count * 3 > end:
                raise GarminOverlayError("Unvollständige FIT-Felder")
            fields = [tuple(source[pos + i * 3:pos + i * 3 + 3])
                      for i in range(count)]
            pos += count * 3
            developer = []
            if header & 0x20:
                if pos >= end:
                    raise GarminOverlayError("FIT-Entwicklerfelder fehlen")
                dev_count = source[pos]
                pos += 1
                if pos + dev_count * 3 > end:
                    raise GarminOverlayError("Unvollständige FIT-Entwicklerfelder")
                developer = [tuple(source[pos + i * 3:pos + i * 3 + 3])
                             for i in range(dev_count)]
                pos += dev_count * 3
            definition = {
                "global": global_num, "endian": endian,
                "fields": fields, "developer": developer,
                "raw": source[begin:pos],
            }
            active[local] = definition
            chunks.append({"kind": "definition", "local": local,
                           "raw": source[begin:pos], "definition": definition})
            continue

        if local not in active:
            raise GarminOverlayError("FIT-Datensatz ohne Definition")
        definition = active[local]
        offsets = {}
        timestamp = None
        for number, size, base in definition["fields"]:
            if pos + size > end:
                raise GarminOverlayError("Unvollständiger FIT-Datensatz")
            offset = pos - begin
            offsets[number] = (offset, size, base, definition["endian"])
            if number == 253:
                number_value = _decoded_scalar(
                    source[pos:pos + size], base, definition["endian"])
                if isinstance(number_value, (int, float)):
                    timestamp = int(number_value)
            pos += size
        for _number, size, _developer_index in definition["developer"]:
            if pos + size > end:
                raise GarminOverlayError("Unvollständige FIT-Entwicklerdaten")
            pos += size
        if compressed:
            previous = last_times.get(local)
            if previous is not None:
                offset = header & 0x1F
                timestamp = (previous & ~31) + offset
                if timestamp < previous:
                    timestamp += 32
        if timestamp is not None:
            last_times[local] = timestamp
        chunks.append({
            "kind": "data", "local": local, "global": definition["global"],
            "raw": source[begin:pos], "definition": definition,
            "offsets": offsets, "timestamp": timestamp,
        })
    if pos != end:
        raise GarminOverlayError("FIT-Blocklänge stimmt nicht")
    return chunks


def _get_numeric(chunk, number):
    spec = chunk.get("offsets", {}).get(number)
    if spec is None:
        return None
    offset, size, typ, endian = spec
    return _decoded_scalar(chunk["raw"][offset:offset + size], typ, endian)


def _patch(chunk, changes):
    """Patch existing scalar FIT fields, preserving all surrounding bytes."""
    if not changes:
        return chunk["raw"]
    data = bytearray(chunk["raw"])
    formats = {
        0: "B", 1: "b", 2: "B", 3: "h", 4: "H",
        5: "i", 6: "I", 10: "B", 11: "H", 12: "I",
        14: "q", 15: "Q", 16: "Q",
    }
    for number, value in changes.items():
        entry = chunk["offsets"].get(number)
        if entry is None or value is None:
            continue
        offset, width, typ, endian = entry
        code = formats.get(typ & 31)
        if code is None or struct.calcsize(code) != width:
            raise GarminOverlayError(
                "Garmin-Zielfeld besitzt eine nicht unterstützte FIT-Kodierung")
        try:
            data[offset:offset + width] = struct.pack(endian + code, int(round(value)))
        except (OverflowError, TypeError, ValueError, struct.error):
            raise GarminOverlayError("Garmin-Zielfeld kann Wert nicht aufnehmen") from None
    return bytes(data)


def _encoded_message(local, global_num, fields):
    """Create a self-contained FIT local definition plus one data message."""
    if len(fields) > 255:
        raise GarminOverlayError("Zu viele zusätzliche FIT-Felder")
    definition = bytearray([0x40 | local, 0, 0])
    definition.extend(struct.pack("<H", global_num))
    definition.append(len(fields))
    body = bytearray([local])
    for number, size, typ, data in fields:
        if size != len(data) or size > 255:
            raise GarminOverlayError("Ungültige SET-Feldlänge")
        definition.extend((number, size, typ))
        body.extend(data)
    return bytes(definition + body)


def _from_message(chunk, local=15):
    """Repackage canonical Speediance SET/title bytes using local ID 15."""
    fields = []
    for number, size, typ in chunk["definition"]["fields"]:
        entry = chunk["offsets"].get(number)
        if entry is None:
            raise GarminOverlayError("Unvollständiger Speediance-SET-Datensatz")
        offset = entry[0]
        fields.append((number, size, typ, chunk["raw"][offset:offset + size]))
    if chunk["definition"]["developer"]:
        raise GarminOverlayError("Unerwartetes SET-Entwicklerfeld")
    return _encoded_message(local, chunk["global"], fields)


def _new_record(timestamp, bpm, local=15):
    return _encoded_message(local, 20, [
        (253, 4, 0x86, struct.pack("<I", timestamp)),
        (3, 1, 2, struct.pack("<B", bpm)),
    ])


def _rebuild(original, stream):
    hs = original[0]
    header = bytearray(original[:hs])
    if len(stream) > 0xFFFFFFFF:
        raise GarminOverlayError("Zusammengeführte FIT-Datei zu groß")
    struct.pack_into("<I", header, 4, len(stream))
    if hs == 14:
        struct.pack_into("<H", header, 12, crc(header[:12]))
    contents = bytes(header) + bytes(stream)
    return contents + struct.pack("<H", crc(contents))


def overlay_garmin_fit(original, speediance, destination, priorities=None,
                       overrides=None, weight_overrides=None,
                       speediance_fit_bytes=None, expected_set_count=None):
    """Use the Garmin FIT as binary base, supplement with Speediance sets.

    The derived *file_id* retains the actual source Garmin manufacturer
    and product while receiving a fresh serial number and creation time for
    each export. Authentic original device_info messages and sensor data are
    retained; the new file remains a separate, edited activity. Garmin Connect
    may still detect identical workout times as duplicate activities.
    """
    from garmin_fit_reader import read_garmin_activity

    priorities = check_priorities(priorities)
    wire = parse_fit_wire(original)
    original_metrics = read_garmin_activity(original)
    merged, meta = merge_workout(speediance, original_metrics, priorities)
    # Privacy-safe relative offsets distinguish estimated SET placement from
    # original Garmin/Speediance sensor timestamps; no dates, IDs or HR data.
    logging.getLogger("speediance_fit").info(
        "Garmin merge set timeline: raw_offset_sec=%d "
        "chosen_offset_sec=%d duration_sec=%d estimated_rebase=%s",
        meta["set_timing_original_offset_seconds"],
        merged["strength_start_offset"],
        meta["duration_seconds"],
        meta["set_timing_aligned_to_activity_start"],
    )
    start = datetime.fromisoformat(merged["started_at"])
    start_ts = stamp(start)
    duration = int(merged["duration_seconds"])
    selected_hr = {
        start_ts + int(elapsed): int(bpm)
        for elapsed, bpm in merged["heart_rate_points"]
    }
    # No set details: preserve native Garmin SET and EXERCISE_TITLE messages.
    # Only actual completed Speediance sets may replace the watch's sets.
    has_completed_sets = any(
        exercise.get("sets") for exercise in speediance.get("exercises") or []
    )
    # A successful Garmin+Speediance merge must contain actual supplied SET
    # messages. The former silent fallback wrote an essentially unchanged
    # Garmin recording while reporting success.
    source_set_count = sum(
        len(ex.get("sets") or [])
        for ex in speediance.get("exercises") or []
    )
    if expected_set_count is not None:
        if (type(expected_set_count) is not int or expected_set_count <= 0
                or expected_set_count != source_set_count):
            raise GarminOverlayError(
                "Die ausgewählte Satzquelle enthält nicht die erwartete Anzahl an Sätzen"
            )
    if not source_set_count and speediance_fit_bytes is None:
        raise GarminOverlayError(
            "Keine abgeschlossenen Speediance-Sätze verfügbar. "
            "Bitte eine passende GM-Manager-History-CSV auswählen; "
            "es wurde keine FIT-Datei erzeugt."
        )
    if speediance_fit_bytes is not None:
        generated = parse_fit_wire(speediance_fit_bytes)
    elif has_completed_sets:
        with TemporaryDirectory(prefix="speediance-merge-") as folder:
            temp_path = write_fit(
                merged, Path(folder) / "speediance-sets.fit",
                overrides=overrides, weight_overrides=weight_overrides,
            )
            generated = parse_fit_wire(temp_path.read_bytes())
    else:
        generated = []
    generated_set_count = sum(
        entry["kind"] == "data" and entry["global"] == 225
        for entry in generated
    )
    if (generated_set_count == 0
            or (source_set_count and generated_set_count != source_set_count)
            or (expected_set_count is not None
                and generated_set_count != expected_set_count)):
        raise GarminOverlayError(
            "Satzübernahme fehlgeschlagen: Die erzeugte FIT enthält "
            "nicht die erwarteten Übungssätze"
        )
    replace_native_sets = True
    new_strength = ([_from_message(entry)
                     for entry in generated if entry["kind"] == "data"
                     and entry["global"] in (225, 264)]
                    if replace_native_sets else [])

    native_times = set()
    original_counts = Counter()
    native_sets = 0
    for item in wire:
        if item["kind"] != "data":
            continue
        original_counts[item["global"]] += 1
        if item["global"] == 225:
            native_sets += 1
        if item["global"] == 20 and item["timestamp"] is not None:
            if _get_numeric(item, 3) is not None:
                native_times.add(item["timestamp"])
    # A multisport/multi-session FIT needs session-level matching rather than
    # one Speediance strength-training block. Never corrupt its other sessions.
    if original_counts[18] != 1:
        raise GarminOverlayError(
            "Nur Garmin-Einzelaktivitäten mit genau einer Sitzung unterstützt"
        )
    # Exactly one physical HR observation per timestamp; original Garmin
    # records are never duplicated solely to overwrite their HR value.
    speed_only = {
        t: hr for t, hr in selected_hr.items()
        if t not in native_times
    }
    record_indices = [(i, item["timestamp"]) for i, item in enumerate(wire)
                      if item["kind"] == "data" and item["global"] == 20
                      and item["timestamp"] is not None]
    record_indices.sort(key=lambda x: x[1])
    record_timestamps = [t for _, t in record_indices]
    additions = defaultdict(list)
    for t, bpm in sorted(speed_only.items()):
        at = bisect_left(record_timestamps, t)
        if at < len(record_indices):
            before = record_indices[at][0]
        elif record_indices:
            before = record_indices[-1][0] + 1
        else:
            before = len(wire)
        additions[before].append(_new_record(t, bpm))
    # Replace the Garmin watch's coarse/orphan SET with the authentic
    # Speediance strength SETs; retain all other Garmin proprietary messages.
    old_strength_index = next(
        (i for i, item in enumerate(wire)
         if item["kind"] == "data" and item["global"] == 225), None
    )
    if old_strength_index is None:
        old_strength_index = next(
            (i for i, item in enumerate(wire)
             if item["kind"] == "data" and item["global"] == 20), len(wire))
    if replace_native_sets:
        additions[old_strength_index].extend(new_strength)

    calories = merged.get("calories")
    summary = merged.get("heart_rate_summary") or {}
    # The original Garmin strength activity can have a coarse, watch-counted
    # total_cycles (field 10). We replaced its SETs with Speediance completed
    # sets, so the session repetition total must not remain at the watch's
    # old value. For timed/dehn movements completionMethod 0/2, 'reps'
    # often means seconds and must not be counted as repetitions.
    actual_reps = 0
    for exercise in speediance.get("exercises") or []:
        try:
            method = exercise.get("completion_method")
            timed = method is not None and int(method) in (0, 2)
        except (TypeError, ValueError):
            timed = False
        if timed:
            continue
        for completed in exercise.get("sets") or []:
            try:
                actual_reps += max(0, int(float(completed.get("reps") or 0)))
            except (TypeError, ValueError, OverflowError):
                pass
    actual_reps = min(4294967294, actual_reps)
    # Only update fields controlled by priority (plus Speediance-owned reps).
    session_changes = {
        10: actual_reps if actual_reps else None,
        11: calories,
        16: summary.get("avg"),
        17: summary.get("max"),
    }
    if priorities["start"] == "speediance":
        session_changes[2] = start_ts
    if priorities["duration"] == "speediance":
        session_changes[7] = duration * 1000
        session_changes[8] = duration * 1000

    # A new FIT must not inherit the Garmin recording's file identity.
    # This is separate from the genuine activity/session/record timestamps.
    file_ids = [entry for entry in wire
                if entry["kind"] == "data" and entry["global"] == 0]
    if len(file_ids) != 1 or not all(
        number in file_ids[0]["offsets"] for number in (1, 2, 3, 4)
    ):
        raise GarminOverlayError(
            "Garmin file_id ohne erforderliche Identitätsfelder")
    # Retain manufacturer and product from the authentic Garmin input.
    # This exact two-field change was tested in Garmin Connect: the
    # 2026-11-13 merged activity recovered its original Training Effect
    # (0.3 aerobic, 0.0 anaerobic, load 4). The former DEVELOPMENT=255,
    # product=0 identifiers suppressed the displayed values despite the
    # SESSION metrics being present byte-for-byte.
    #
    # Keep an independent derived file identity (new serial/created time)
    # and preserve every original device_info message unchanged. Do not
    # invent a different Garmin product or manufacturer for non-Garmin FITs.
    original_manufacturer = _get_numeric(file_ids[0], 1)
    original_product = _get_numeric(file_ids[0], 2)
    if original_manufacturer is None or original_product is None:
        raise GarminOverlayError(
            "Garmin file_id ohne gültige Hersteller-/Produktkennung")
    original_serial = _get_numeric(file_ids[0], 3)
    original_created = _get_numeric(file_ids[0], 4)
    derivative_serial = randbits(32)
    while not derivative_serial or derivative_serial == original_serial:
        derivative_serial = randbits(32)
    derivative_created = stamp(datetime.now(timezone.utc))
    if derivative_created == original_created:
        derivative_created += 1
    definitions = {}
    out = bytearray()
    patched_hr = 0
    for i in range(len(wire) + 1):
        if i in additions:
            for blob in additions[i]:
                out.extend(blob)
            # Local ID 15 must be restored or later original Garmin
            # data messages referencing it would be misinterpreted.
            if 15 in definitions:
                out.extend(definitions[15])
        if i == len(wire):
            break
        item = wire[i]
        if item["kind"] == "definition":
            definitions[item["local"]] = item["raw"]
            out.extend(item["raw"])
            continue
        num = item["global"]
        if replace_native_sets and num in (225, 264):
            # Garmin exercise titles refer to the original SETs and may
            # clash with the Speediance custom exercise-title mapping.
            continue
        changes = {}
        if num == 0:
            # Preserve the verified source device's manufacturer/product
            # while giving this edited, derived FIT its own identity. Do not
            # override the actual Garmin watch's device_info messages.
            changes = {
                1: original_manufacturer, 2: original_product,
                3: derivative_serial, 4: derivative_created,
            }
        elif num == 18:
            changes = session_changes
        elif num == 19 and original_counts[19] == 1:
            # Multi-lap Garmin summaries are distinct real measurements:
            # never replace EACH lap's values with whole-session totals.
            changes = {10: actual_reps if actual_reps else None,
                       11: calories, 15: summary.get("avg"),
                       16: summary.get("max")}
            if priorities["duration"] == "speediance":
                changes.update({7: duration * 1000, 8: duration * 1000})
            if priorities["start"] == "speediance":
                changes[2] = start_ts
        elif num == 34 and priorities["duration"] == "speediance":
            changes = {0: duration * 1000}
        elif num == 20 and item["timestamp"] in selected_hr:
            # Garmin remains untouched by default; when Speediance wins,
            # patch the original HR *inside* its native record, retaining
            # all other fields, developer telemetry and Garmin sensors.
            existing = _get_numeric(item, 3)
            chosen = selected_hr[item["timestamp"]]
            if existing is not None and existing != chosen:
                changes = {3: chosen}
                patched_hr += 1
        out.extend(_patch(item, changes))

    result = _rebuild(original, out)
    # Parse and CRC-validate *the final emitted FIT*, not just the input.
    final = parse_fit_wire(result)
    final_counts = Counter(
        x["global"] for x in final if x["kind"] == "data")
    expected_strength = sum(
        1 for x in generated if x["kind"] == "data" and x["global"] == 225)
    if final_counts[225] != generated_set_count:
        raise GarminOverlayError("SET-Anzahl nach Garmin-Overlay inkonsistent")
    if expected_set_count is not None and final_counts[225] != expected_set_count:
        raise GarminOverlayError(
            "Export abgebrochen: Die zusammengeführte FIT enthält "
            "nicht die erwartete Anzahl an Übungssätzen"
        )
    if speediance.get("_set_source") == "gm_manager_history_csv":
        # Check decoded final FIT, not just the temporary generated FIT.
        # A plan- or Garmin-only file must never be accepted as a CSV merge.
        planned = [item for exercise in speediance.get("exercises") or []
                   for item in exercise.get("sets") or []]
        written = [item for item in final if item["kind"] == "data"
                   and item["global"] == 225]
        if len(written) != len(planned):
            raise GarminOverlayError("CSV-Sätze fehlen in der finalen FIT-Datei")
        for given, emitted in zip(planned, written):
            reps = max(0, min(65534, int(float(given.get("reps") or 0))))
            kg = max(0.0, float(given.get("weight") or 0))
            weight_scaled = min(65534, round(kg * 16))
            if (_get_numeric(emitted, 3) != reps
                    or _get_numeric(emitted, 4) != weight_scaled):
                raise GarminOverlayError(
                    "Export abgebrochen: CSV-Wiederholungen oder -Gewichte "
                    "stimmen in der FIT-Datei nicht überein"
                )
    emitted_ids = [x for x in final if x["kind"] == "data" and x["global"] == 0]
    if len(emitted_ids) != 1 or any(
        _get_numeric(emitted_ids[0], number) != value
        for number, value in (
            (1, original_manufacturer), (2, original_product),
            (3, derivative_serial), (4, derivative_created),
        )
    ):
        raise GarminOverlayError("Neue FIT-Dateiidentität konnte nicht gesetzt werden")
    for num, count in original_counts.items():
        if num not in (225, 20, 264) and final_counts[num] != count:
            raise GarminOverlayError("Garmin-Originaldaten gingen beim Merge verloren")
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    meta.update({
        "garmin_original_messages": sum(original_counts.values()),
        "garmin_preserved_message_types": len(original_counts),
        "garmin_device_info": original_counts[23],
        "new_speediance_sets": expected_strength,
        "preserved_native_sets": native_sets if not replace_native_sets else 0,
        "speediance_repetitions": actual_reps,
        "replaced_garmin_sets": native_sets if replace_native_sets else 0,
        "added_hr_records": len(speed_only),
        "patched_hr_records": patched_hr,
        "output_bytes": len(result),
        "file_id_changed": True,
        "speediance_source": ("saved_fit" if speediance_fit_bytes is not None
                             else "gm_manager_history_csv"
                             if speediance.get("_set_source") == "gm_manager_history_csv"
                             else "gm_manager_confirmed"
                             if speediance.get("_set_source") == "gm_manager_confirmed"
                             else "cloud"),
    })
    return target, meta
