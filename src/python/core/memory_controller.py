"""1. Utility for reading game memory.

This module provides a :class:`MemoryController` that attaches to the
Stardew Valley process and exposes convenience methods for resolving
pointer chains.  The ``read_energy`` method is implemented using the
pointer chain supplied via Cheat Engine.

basically, this attached to stardew valley process using pymem, 
it looks through pointer chains and exposes read_energy, read_health, etc to retreive player stats that will be used in the trainer

The pointer values are placeholders and will need to be updated for the
player's current game version.
"""

#dont wrap these in try/except, because these are standard library imports
from dataclasses import dataclass
from typing import Optional
import struct
from src.python.core.io.process_client import ProcessClient


#@dataclass is a decorator that creates a class with default values for its attributes
@dataclass
class PointerChain: 
    """Represents a pointer chain to a value in memory."""
    module: str
    base_offset: int
    offsets: list[int]

class MemoryController:
    """Controller for reading and writing to game memory."""

    #these persist outside of the class, they are constants
    PROCESS_NAME = "StardewValley.exe"
    # Note: These pointers are examples and need to be updated for the current game version
    ENERGY_PTR = PointerChain("StardewValley.exe", 0X00349A98, [0x70, 0xA0, 0x88, 0x4D0, 0x4C])
    
    #init automatically runs whenever you make a controller with = MemoryController(), 
    #meaning each memorycontroller will have its own pymem instance and module instance
    def __init__(self): 
        self.client = ProcessClient()
        self.attached = False

    def attach(self) -> bool:
        """Attempt to attach to the game process."""
        if self.client.attach(self.PROCESS_NAME):
            self.attached = True
            return True
        return False

    def detach(self):
        self.client.detach()
        self.attached = False

    def _read_u64(self, addr: int) -> int:
        data = self.client.read_memory(addr, 8)
        if len(data) == 8:
            return struct.unpack("<Q", data)[0]
        return 0

    def _read_float(self, addr: int) -> float:
        data = self.client.read_memory(addr, 4)
        if len(data) == 4:
            return struct.unpack("<f", data)[0]
        return 0.0

    #-----------------------------
    # Pointer Utilities
    #-----------------------------
    def _resolve_pointer(self, chain: PointerChain) -> int: 
        """Return the absolute address for the pointer chain."""
        if not self.attached:
            return 0

        # For now, assuming base address is just the module base. 
        # In a real scenario, we need to get the module base address.
        # ProcessClient doesn't expose module enumeration yet.
        # We might need to add that to C lib or just use a fixed base if ASLR is off (unlikely).
        # For this exercise, let's assume the user provides a full address or we need to implement module finding.
        
        # TODO: Implement module base finding in C library.
        # For now, let's assume the base_offset is from the process base (which might be 0x140000000 or similar).
        # But wait, the design doc says "static base + offsets".
        
        # If we can't get module base, we can't reliably resolve relative pointers.
        # Let's assume for now we just use the pointer chain as is, but we really need GetModuleHandle.
        
        # Placeholder: using 0 as module base (incorrect for ASLR)
        module_base = 0 
        
        addr = self._read_u64(module_base + chain.base_offset)
        for offset in chain.offsets: 
            addr = self._read_u64(addr + offset)
        return addr


    #-----------------------------
    # Public API
    #-----------------------------
    def read_energy(self) -> Optional[float]:
        """Read and return the players current energy level."""
        if not self.attached:
            return None
        try:
            addr = self._resolve_pointer(self.ENERGY_PTR)
            return self._read_float(addr)
        except Exception:
            return None