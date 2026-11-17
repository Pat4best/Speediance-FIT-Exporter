"""Privacy-safe structural inspection for one Speediance API response.

Never record IDs, values, timestamps, names, credentials, body strings, or
full JSON. Only conservative field paths, scalar types and array sizes.
"""
import json
import re

_SAFE_FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,49}\Z")
MAX_NODES = 160
MAX_DEPTH = 7


def response_structure(value):
    """Return a bounded list of paths/types; never serialize any scalar value."""
    result = []
    seen = set()

    def add(path, description):
        marker = (path, description)
        if marker not in seen and len(result) < MAX_NODES:
            seen.add(marker)
            result.append({"path": path, "shape": description})

    def visit(node, path, depth):
        if len(result) >= MAX_NODES:
            return
        if isinstance(node, dict):
            add(path, "object")
            if depth >= MAX_DEPTH:
                return
            for key, child in list(node.items())[:80]:
                # Server-provided object keys might be user-controlled.
                # Do not print free-form, numeric, UUID, email, or long keys.
                if (not isinstance(key, str) or not _SAFE_FIELD.fullmatch(key)
                        or sum(c.isdigit() for c in key) > 3):
                    continue
                visit(child, path + "." + key, depth + 1)
        elif isinstance(node, (list, tuple)):
            add(path, "array[%d]" % len(node))
            if depth >= MAX_DEPTH:
                return
            # Merge schemas for several examples, not only element 0.
            for element in node[:3]:
                visit(element, path + "[]", depth + 1)
        elif node is None:
            add(path, "null")
        elif isinstance(node, bool):
            add(path, "boolean")
        elif isinstance(node, (int, float)):
            add(path, "number")
        elif isinstance(node, str):
            add(path, "string")
        else:
            add(path, "other")

    visit(value, "$", 0)
    return result


def structural_log(value):
    """JSON for a log entry: guaranteed to contain metadata only."""
    return json.dumps(response_structure(value), ensure_ascii=True,
                      separators=(",", ":"))
