"""Identify a heart-rate sensor only from explicit Speediance device metadata.

A watchType code or nonzero BPM reading does not identify the manufacturer or
model; neither is sufficient to invent 'Garmin HRM 600'. Do not extract MACs,
UUIDs or serial numbers into FIT metadata.
"""
import re

_DIRECT_FIELDS = {
    "heartratedevicename", "heartratesensorname", "heartratemonitorname",
    "hrdevicename", "hrsensorname", "hrmonitorname",
    "watchname", "watchmodel", "pulsesensorname",
}
_SENSOR_OBJECTS = {
    "heartratedevice", "heartratesensor", "heartratemonitor",
    "hrdevice", "hrsensor", "hrmonitor", "watch", "sensor",
}
_NAME_FIELDS = {"name", "model", "modelname", "devicename", "productname"}
_PROTOCOL_FIELDS = {"protocol", "connectiontype", "connecttype", "transport"}
_MFG_FIELDS = {"manufacturer", "vendor", "brand"}

def _key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _clean_name(value):
    if not isinstance(value, str):
        return None
    value = " ".join(value.strip().split())
    if (not 3 <= len(value) <= 80 or
            value.casefold() in {"unknown", "null", "none", "watch", "sensor"} or
            "@" in value or
            re.search(r"(?:[a-f0-9]{2}[:-]){5}[a-f0-9]{2}|[a-f0-9]{8}-[a-f0-9]{4}-", value, re.I)):
        return None
    return value


def _protocol(value):
    if not isinstance(value, str):
        return None
    name = _key(value)
    if name in {"ble", "bluetoothlowenergy", "bluetoothle"}:
        return "ble"
    if name in {"ant", "antplus"}:
        return "antplus"
    return None


def _sensor(name, context=None):
    name = _clean_name(name)
    if name is None:
        return None
    context = context if isinstance(context, dict) else {}
    metadata = {_key(k): v for k, v in context.items()}
    vendor = next((metadata[k] for k in _MFG_FIELDS if k in metadata), None)
    return {
        "name": name,
        "manufacturer": (
            "Garmin" if name.casefold().startswith("garmin ") or
            (isinstance(vendor, str) and vendor.strip().casefold() == "garmin")
            else None
        ),
        "protocol": next((_protocol(metadata[k]) for k in _PROTOCOL_FIELDS
                          if k in metadata and _protocol(metadata[k])), None),
        "verified_from": "speediance_metadata",
    }


def find_hr_sensor(payload):
    """Extract only an explicitly named HR device from a bounded data tree."""
    def walk(node, depth):
        if depth > 7:
            return None
        if isinstance(node, dict):
            for raw_key, val in node.items():
                key = _key(raw_key)
                if key in _DIRECT_FIELDS:
                    if isinstance(val, str):
                        sensor = _sensor(val, node)
                        if sensor:
                            return sensor
                    elif isinstance(val, dict):
                        candidate = walk_sensor_object(val)
                        if candidate:
                            return candidate
                if key in _SENSOR_OBJECTS and isinstance(val, dict):
                    candidate = walk_sensor_object(val)
                    if candidate:
                        return candidate
            for val in node.values():
                if isinstance(val, (dict, list)):
                    candidate = walk(val, depth + 1)
                    if candidate:
                        return candidate
        elif isinstance(node, list):
            for item in node[:100]:
                candidate = walk(item, depth + 1)
                if candidate:
                    return candidate
        return None

    def walk_sensor_object(node):
        fields = {_key(k): v for k, v in node.items()}
        for k in _NAME_FIELDS:
            if k in fields:
                result = _sensor(fields[k], node)
                if result:
                    return result
        return None

    return walk(payload, 0)


def user_confirmed_sensor(display_name):
    """Create FIT sensor label from explicit user input, not inferred telemetry.

    In screenshots Speediance displays HRM600:654360; the suffix may be an
    ANT+ device number but is *not* necessarily the serial number. Keep it as
    a descriptor only and do not populate serial_number/product enums.
    """
    raw = _clean_name(display_name)
    if not raw:
        return None
    if re.fullmatch(r"HRM\s*600(?::\d{1,10})?", raw, re.IGNORECASE):
        return {
            "name": "Garmin HRM 600",
            "descriptor": raw,
            "manufacturer": "Garmin",
            "protocol": None,
            "verified_from": "user_confirmed",
        }
    return {
        "name": raw,
        "descriptor": raw,
        "manufacturer": ("Garmin" if raw.casefold().startswith("garmin ") else None),
        "protocol": None,
        "verified_from": "user_confirmed",
    }
