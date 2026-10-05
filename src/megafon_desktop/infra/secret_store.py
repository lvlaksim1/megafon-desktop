from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path
from typing import Protocol

from .paths import secrets_dir


class SecretStore(Protocol):
    def set(self, key: str, value: str) -> None: ...
    def get(self, key: str) -> str | None: ...
    def delete(self, key: str) -> None: ...


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buf = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))), buf


class WindowsDpapiSecretStore:
    """Per-user secret files encrypted by Windows DPAPI.

    Ciphertext may be stored on disk safely for the normal local-user threat model; decrypting it
    requires the same Windows user context. No password or encryption key is stored in SQLite.
    """

    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    def __init__(self, root: Path | None = None) -> None:
        if os.name != "nt":
            raise RuntimeError("Windows DPAPI is only available on Windows")
        self.root = root or secrets_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self._crypt32 = ctypes.windll.crypt32
        self._kernel32 = ctypes.windll.kernel32
        self._crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB), ctypes.c_wchar_p, ctypes.POINTER(_DATA_BLOB),
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DATA_BLOB),
        ]
        self._crypt32.CryptProtectData.restype = wintypes.BOOL
        self._crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB), ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(_DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p,
            wintypes.DWORD, ctypes.POINTER(_DATA_BLOB),
        ]
        self._crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p

    def _path(self, key: str) -> Path:
        safe = "".join(ch for ch in key if ch.isalnum() or ch in "-_.")
        if not safe or safe != key:
            raise ValueError("invalid secret key")
        return self.root / f"{safe}.bin"

    def _protect(self, plaintext: bytes) -> bytes:
        in_blob, in_buf = _blob(plaintext)
        out_blob = _DATA_BLOB()
        ok = self._crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            "Megafon Desktop",
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(out_blob),
        )
        _ = in_buf
        if not ok:
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            self._kernel32.LocalFree(out_blob.pbData)

    def _unprotect(self, ciphertext: bytes) -> bytes:
        in_blob, in_buf = _blob(ciphertext)
        out_blob = _DATA_BLOB()
        ok = self._crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(out_blob),
        )
        _ = in_buf
        if not ok:
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            self._kernel32.LocalFree(out_blob.pbData)

    def set(self, key: str, value: str) -> None:
        path = self._path(key)
        temp = path.with_suffix(".tmp")
        temp.write_bytes(self._protect(value.encode("utf-8")))
        os.replace(temp, path)

    def get(self, key: str) -> str | None:
        path = self._path(key)
        if not path.exists():
            return None
        return self._unprotect(path.read_bytes()).decode("utf-8")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


class MemorySecretStore:
    """Test-only secret store."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def delete(self, key: str) -> None:
        self.values.pop(key, None)
