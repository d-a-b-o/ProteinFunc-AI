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

            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            proc = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(proc, ctypes.byref(counters), counters.cb):
                return counters.PeakWorkingSetSize / 2**20
            return None
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / 2**20 if sys.platform == "darwin" else peak / 1024  # macOS: bytes; Linux: KB
    except Exception:  # noqa: BLE001 - la medición es informativa
        return None


def cpu_count() -> int:
    return os.cpu_count() or 1
