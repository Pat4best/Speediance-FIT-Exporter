"""Windows Credential Manager storage for opt-in Speediance login credentials.

Windows generic credentials are scoped to the current Windows user.
We never keep passwords or tokens in application JSON, logs, or source code.
"""
import ctypes
import os
from ctypes import wintypes

TARGET = "SpeedianceFITExporter/SpeedianceLogin"
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168


class FILETIME(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _advapi():
    if os.name != "nt":
        raise RuntimeError("Windows-Anmeldeinformationsmanager ist nur unter Windows verfügbar")
    lib = ctypes.WinDLL("Advapi32", use_last_error=True)
    lib.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    lib.CredWriteW.restype = wintypes.BOOL
    lib.CredReadW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(CREDENTIALW)),
    ]
    lib.CredReadW.restype = wintypes.BOOL
    lib.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    lib.CredDeleteW.restype = wintypes.BOOL
    lib.CredFree.argtypes = [ctypes.c_void_p]
    lib.CredFree.restype = None
    return lib


def save_login(email, password, region):
    """Store only on explicit opt-in. Raises OSError on OS failure."""
    if not email or not password or region not in ("EU", "Global"):
        raise ValueError("Unvollständige Anmeldedaten")
    raw = password.encode("utf-16-le")
    if len(raw) > 2560:
        raise ValueError("Passwort überschreitet Windows Credential Manager Limit")
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    cred = CREDENTIALW()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = TARGET
    cred.Comment = region
    cred.CredentialBlobSize = len(raw)
    cred.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.UserName = email
    lib = _advapi()
    if not lib.CredWriteW(ctypes.byref(cred), 0):
        raise ctypes.WinError(ctypes.get_last_error())


def load_login():
    """Return (email, password, region), or None when not saved."""
    lib = _advapi()
    ptr = ctypes.POINTER(CREDENTIALW)()
    if not lib.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(ptr)):
        err = ctypes.get_last_error()
        if err == ERROR_NOT_FOUND:
            return None
        raise ctypes.WinError(err)
    try:
        credential = ptr.contents
        size = int(credential.CredentialBlobSize)
        raw = ctypes.string_at(credential.CredentialBlob, size) if size else b""
        password = raw.decode("utf-16-le")
        region = credential.Comment if credential.Comment in ("EU", "Global") else "EU"
        return credential.UserName or "", password, region
    finally:
        lib.CredFree(ctypes.cast(ptr, ctypes.c_void_p))


def delete_login():
    """Forget the stored Windows credential without changing Speediance."""
    lib = _advapi()
    if not lib.CredDeleteW(TARGET, CRED_TYPE_GENERIC, 0):
        err = ctypes.get_last_error()
        if err != ERROR_NOT_FOUND:
            raise ctypes.WinError(err)
