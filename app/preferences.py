"""Small local user preferences. No passwords, tokens or account IDs here."""
from pathlib import Path
import json
import os
from exercise_mapping import normalize, UNKNOWN


DEFAULT_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SpeedianceFITExporter"


def _read(path):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (FileNotFoundError, ValueError, OSError, UnicodeError):
        return {}


def _save(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)




# This is just a non-secret UI setting (never put access tokens here).
CLIENT_TYPES = ("bike", "nano", "phone")


def load_login_client_type(root=DEFAULT_ROOT):
    value = _read(Path(root) / "settings.json").get("login_client_type")
    return value if value in CLIENT_TYPES else "bike"


def save_login_client_type(value, root=DEFAULT_ROOT):
    if value not in CLIENT_TYPES:
        raise ValueError("Unbekannter Speediance-Anmeldetyp")
    settings = _read(Path(root) / "settings.json")
    settings["login_client_type"] = value
    _save(Path(root) / "settings.json", settings)




LANGUAGES = ("de", "en")


def load_language(root=DEFAULT_ROOT):
    value = _read(Path(root) / "settings.json").get("language")
    return value if value in LANGUAGES else "de"


def save_language(language, root=DEFAULT_ROOT):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    settings = _read(Path(root) / "settings.json")
    settings["language"] = language
    _save(Path(root) / "settings.json", settings)


def load_catalog_language(root=DEFAULT_ROOT):
    """Exercise-picker locale, defaults to the app's chosen language."""
    settings = _read(Path(root) / "settings.json")
    value = settings.get("catalog_language")
    if value in LANGUAGES:
        return value
    value = settings.get("language")
    return value if value in LANGUAGES else "de"


def save_catalog_language(language, root=DEFAULT_ROOT):
    if language not in LANGUAGES:
        raise ValueError("Unsupported catalog language")
    settings = _read(Path(root) / "settings.json")
    settings["catalog_language"] = language
    _save(Path(root) / "settings.json", settings)


def export_folder(root=DEFAULT_ROOT):
    value = _read(Path(root) / "settings.json").get("export_folder")
    return value if isinstance(value, str) else ""


def save_export_folder(path, root=DEFAULT_ROOT):
    folder = Path(path).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError("Der Exportordner existiert nicht")
    settings = _read(Path(root) / "settings.json")
    settings["export_folder"] = str(folder)
    _save(Path(root) / "settings.json", settings)


def _mapping_path(root):
    return Path(root) / "exercise_mappings.json"


def saved_mappings(root=DEFAULT_ROOT):
    raw = _read(_mapping_path(root)).get("overrides", {})
    overrides = {}
    if not isinstance(raw, dict):
        return overrides
    for name, value in raw.items():
        if not isinstance(name, str) or not isinstance(value, list) or len(value) != 2:
            continue
        try:
            cat, sub = map(int, value)
            if 0 <= cat <= UNKNOWN and 0 <= sub <= 65534:
                overrides[normalize(name)] = (cat, sub)
        except (ValueError, TypeError):
            continue
    return overrides


def observed_names(root=DEFAULT_ROOT):
    value = _read(_mapping_path(root)).get("names", [])
    return sorted(set(n.strip() for n in value if isinstance(n, str) and n.strip())) if isinstance(value, list) else []


def remember_names(names, root=DEFAULT_ROOT):
    file = _mapping_path(root)
    data = _read(file)
    existing = set(observed_names(root))
    existing.update(str(n).strip() for n in names if n and str(n).strip())
    data["names"] = sorted(existing)
    _save(file, data)


def set_override(name, category, subtype, root=DEFAULT_ROOT):
    key = normalize(name)
    if not key:
        raise ValueError("Übungsname darf nicht leer sein")
    file = _mapping_path(root)
    data = _read(file)
    overrides = saved_mappings(root)
    if category is None:
        overrides.pop(key, None)
    else:
        cat, sub = int(category), int(subtype)
        if not (0 <= cat <= UNKNOWN and 0 <= sub <= 65534):
            raise ValueError("Ungültige Garmin-FIT-Übungs-ID")
        overrides[key] = (cat, sub)
    data["overrides"] = {k: list(v) for k, v in overrides.items()}
    names = set(observed_names(root))
    names.add(name.strip())
    data["names"] = sorted(names)
    _save(file, data)


def saved_weight_multipliers(root=DEFAULT_ROOT):
    """Explicit per-exercise multiplier for fallback single-weight API values."""
    raw = _read(_mapping_path(root)).get("weight_multipliers", {})
    result = {}
    if isinstance(raw, dict):
        for name, value in raw.items():
            if isinstance(name, str) and type(value) is int and value in (1, 2):
                key = normalize(name)
                if key:
                    result[key] = value
    return result


def set_weight_multiplier(name, multiplier, root=DEFAULT_ROOT):
    """Remember x1/x2 independently of Garmin exercise IDs.

    Explicit x1 is retained to override the automatic dual-handle x2 guess.
    """
    key = normalize(name)
    if not key:
        raise ValueError("Übungsname darf nicht leer sein")
    if type(multiplier) is not int or multiplier not in (1, 2):
        raise ValueError("Gewichtsfaktor muss 1 oder 2 sein")
    path = _mapping_path(root)
    data = _read(path)
    values = saved_weight_multipliers(root)
    values[key] = multiplier
    data["weight_multipliers"] = values
    names = set(observed_names(root))
    names.add(name.strip())
    data["names"] = sorted(names)
    _save(path, data)


def saved_merge_priorities(root=DEFAULT_ROOT):
    """No secret material: preferred source for each merged FIT metric."""
    from garmin_merge import DEFAULT_PRIORITIES, check_priorities
    found = _read(Path(root) / "settings.json").get("merge_priorities")
    if not isinstance(found, dict):
        return dict(DEFAULT_PRIORITIES)
    safe = {k: v for k, v in found.items()
            if k in DEFAULT_PRIORITIES and v in ("garmin", "speediance")}
    return check_priorities(safe)


def save_merge_priorities(priorities, root=DEFAULT_ROOT):
    from garmin_merge import check_priorities
    cleaned = check_priorities(priorities)
    settings = _read(Path(root) / "settings.json")
    settings["merge_priorities"] = cleaned
    _save(Path(root) / "settings.json", settings)
