import ctypes
from ctypes import wintypes
import glob
import os
from pathlib import Path

class ProcessClient:
    def __init__(self):
        self.lib = self._load_library()
        self._setup_signatures()
        self.process_handle = None
        self.pid = 0

    def _load_library(self):
        # Find the compiled extension (.pyd) in the current directory
        current_dir = Path(__file__).parent.parent
        # Look for clib*.pyd
        pyd_files = list(current_dir.glob("clib*.pyd"))
        if not pyd_files:
            raise FileNotFoundError("Could not find compiled C library (clib*.pyd)")
        
        # Load the library using ctypes
        return ctypes.CDLL(str(pyd_files[0]))

    def _setup_signatures(self):
        # gt_process_t struct
        class GTProcess(ctypes.Structure):
            _fields_ = [
                ("handle", wintypes.HANDLE),
                ("pid", wintypes.DWORD),
                ("is64bit", ctypes.c_bool),
            ]
        self.GTProcess = GTProcess

        # gt_find_process_id
        self.lib.gt_find_process_id.argtypes = [ctypes.c_char_p, ctypes.POINTER(wintypes.DWORD)]
        self.lib.gt_find_process_id.restype = ctypes.c_bool

        # gt_open_process
        self.lib.gt_open_process.argtypes = [wintypes.DWORD, ctypes.POINTER(GTProcess)]
        self.lib.gt_open_process.restype = ctypes.c_bool

        # gt_close_process
        self.lib.gt_close_process.argtypes = [ctypes.POINTER(GTProcess)]
        self.lib.gt_close_process.restype = None

        # gt_read
        self.lib.gt_read.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
        self.lib.gt_read.restype = ctypes.c_bool

        # gt_write
        self.lib.gt_write.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_void_p, ctypes.c_size_t]
        self.lib.gt_write.restype = ctypes.c_bool

    def attach(self, process_name: str) -> bool:
        pid = wintypes.DWORD()
        name_bytes = process_name.encode('utf-8')
        if not self.lib.gt_find_process_id(name_bytes, ctypes.byref(pid)):
            return False
        
        self.process_struct = self.GTProcess()
        if self.lib.gt_open_process(pid, ctypes.byref(self.process_struct)):
            self.process_handle = self.process_struct.handle
            self.pid = pid.value
            return True
        return False

    def detach(self):
        if self.process_handle:
            self.lib.gt_close_process(ctypes.byref(self.process_struct))
            self.process_handle = None
            self.pid = 0

    def read_memory(self, address: int, size: int) -> bytes:
        if not self.process_handle:
            raise RuntimeError("Not attached to a process")
        
        buffer = ctypes.create_string_buffer(size)
        if self.lib.gt_read(self.process_handle, ctypes.c_void_p(address), buffer, size):
            return buffer.raw
        return b""

    def write_memory(self, address: int, data: bytes) -> bool:
        if not self.process_handle:
            raise RuntimeError("Not attached to a process")
        
        buffer = ctypes.create_string_buffer(data)
        return self.lib.gt_write(self.process_handle, ctypes.c_void_p(address), buffer, len(data))
