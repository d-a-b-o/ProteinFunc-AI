"""Medición de recursos de una ejecución (RNF-05), sin dependencias externas."""
from __future__ import annotations

import os
import sys


def peak_memory_mb() -> float | None:
    """Memoria residente máxima del proceso desde su inicio, en MB (None si no se puede medir)."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            # Declarar tipos: sin ellos ctypes trunca el handle de 64 bits a int de 32 bits.
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.GetCurrentProcess.argtypes = []
            get_info = kernel32.K32GetProcessMemoryInfo  # Windows 7+; equivale a psapi.GetProcessMemoryInfo
            get_info.restype = wintypes.BOOL
            get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]

            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            if get_info(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return counters.PeakWorkingSetSize / 2**20
            return None
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / 2**20 if sys.platform == "darwin" else peak / 1024  # macOS: bytes; Linux: KB
    except Exception:  # noqa: BLE001 - la medición es informativa
        return None


def cpu_count() -> int:
    return os.cpu_count() or 1
