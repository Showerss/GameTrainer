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
from typing import Iterable, Optional
from __future__ import annotations

#try to import pymem, if it fails raise an error, this should be industry standard
try: 
    from pymem import Pymem
    from pymem.process import module_from_name
except ImportError as e:
    raise ImportError("pymem is required for memory access. Please install it using pip.") from e


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
    ENERGY_PTR = PointerChain("StardewValley.exe", 0X00349A98, [0x70, 0xA0, 0x88, 0x4D0, 0x4C])
    #TODO: find the below pointers 
    HEALTH_PTR = NONE
    MONEY_PTR = NONE
    INVENTORY_PTR = NONE

    #init automatically runs whenever you make a controller with = MemoryController(), 
    #meaning each memorycontroller will have its own pymem instance and module instance
    def __init__(self): 
        if Pymem is None or module_from_name is None: 
            raise ImportError("pymem is required for memory access. Please install it using pip.")
        self.pm = Pymem(self.PROCESS_NAME)
        self.module = module_from_name(self.pm.process_handle, self.MODULE_NAME)


    #-----------------------------
    # Pointer Utilities
    #-----------------------------
    def _resolve_pointer(self, chain: PointerChain) -> int: 
        """return the absolute address for the pointer chain"""

        module_base = module_from_name(self.pm.process_handle, chain.module).lpBaseOfDll #this gives me the address of the games main building (.exe)... lpBaseOfDll is the memory address from where the game loads up
        addr = self.pm.read_ulonglong(module_base + chain.base_offset) #module base + base offset is the specific room of the building
        for offset in chain.offsets: 
            addr = self.pm.read_ulonglong(addr + offset)
        return addr


    #-----------------------------
    # Public API
    #-----------------------------
    def read_energy(self) -> Optional[float]:
        """Read and return the players currernt energy level"""

        try:
            addr = self._resolve_pointer(self.ENERGY_PTR)
            return self.pm.read_float(addr)
        except:
            return None
    
    def read_health(self) -> Optional[float]:
        """Read and return the players currernt health level"""
    
    def read_money(self) -> Optional[int]:
        """Read and return the players currernt money level"""
    
    def read_inventory(self) -> Optional[list[str]]:
        """Read and return the players currernt inventory"""