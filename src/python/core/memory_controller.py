from __future__ import annotations

"""Utility for reading game memory.

This module provides a :class:`MemoryController` that attaches to the
Stardew Valley process and exposes convenience methods for resolving
pointer chains.  The ``read_energy`` method is implemented using the
pointer chain supplied via Cheat Engine.

The pointer values are placeholders and will need to be updated for the
player's current game version.
"""

from dataclasses import dataclass
from typing import Iterable, Optional


#try to import pymem, if it fails raise an error
try: 
    from pymem import Pymem
    from pymem.process import module_from_name
except ImportError:
    raise ImportError("pymem is required for memory access. Please install it using pip.")
    Pymem = None
    module_from_name = None



@dataclass
class PointerChain: 
    """Represents a pointer chain to a value in memory."""
    module: str
    base_offset: int
    offsets: list[int]

class MemoryController:
    """Controller for reading and writing to game memory."""
    

    PROCESS_NAME = "StardewValley.exe"
    
    
    ENERGY_PTR = PointerChain("StardewValley.exe", 0X00349A98, [0x70, 0xA0, 0x88, 0x4D0, 0x4C])
    
    #TODO: find these pointers 
    HEALTH_PTR = NONE
    MONEY_PTR = NONE
    INVENTORY_PTR = NONE

    def __init__(self): 
        if Pymem is None or module_from_name is None: 
            raise ImportError("pymem is required for memory access. Please install it using pip.")
        self.pm = Pymem(self.PROCESS_NAME)
        self.module = module_from_name(self.pm.process_handle, self.MODULE_NAME)









pm = Pymem(PROCESS_NAME)
module = module_from_name(pm.process_handle, MODULE_NAME)
addr = pm.read_ulonglong(module + BASE_OFFSET)



#read energy
for offset in OFFSETS:
    addr = pm.read_ulonglong(addr + offset) #use ulonglong becaues stardew is a 64 bit process


energy = pm.read_float(addr)

print(energy)


#read health

#read inventory

#read money