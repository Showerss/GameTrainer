#include "memory_manager.h"
#include <tlhelp32.h>
#include <iostream>

namespace GameTrainer {

Process::Process() {}

Process::~Process() {
    Detach();
}

Process::Process(Process&& other) noexcept {
    *this = std::move(other);
}

Process& Process::operator=(Process&& other) noexcept {
    if (this != &other) {
        Detach();
        handle_ = other.handle_;
        pid_ = other.pid_;
        is64bit_ = other.is64bit_;
        
        other.handle_ = nullptr;
        other.pid_ = 0;
        other.is64bit_ = false;
    }
    return *this;
}

bool Process::Attach(const std::string& name) {
    DWORD pid = 0;
    if (!gt_find_process_id(name.c_str(), &pid)) return false;
    return Attach(pid);
}

bool Process::Attach(DWORD pid) {
    Detach(); // Close existing if any
    
    // TEACHER NOTE: specific access rights are required to read/write memory
    // PROCESS_VM_READ: Allows reading memory
    // PROCESS_VM_WRITE: Allows writing memory
    // PROCESS_VM_OPERATION: Allows VirtualProtectEx (changing memory protection)
    handle_ = OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION, FALSE, pid);
    if (!handle_) return false;
    
    pid_ = pid;
    
    // Check architecture
    BOOL isWow64 = FALSE;
    // TEACHER NOTE: "Wow64" stands for "Windows on Windows 64-bit".
    // It has nothing to do with World of Warcraft! :)
    // It checks if a 32-bit program is running on 64-bit Windows.
    if (IsWow64Process(handle_, &isWow64)) {
        is64bit_ = !isWow64;
    } else {
        // Fallback or error handling
        is64bit_ = false; 
    }
    
    return true;
}

void Process::Detach() {
    if (handle_) {
        CloseHandle(handle_);
        handle_ = nullptr;
    }
    pid_ = 0;
    is64bit_ = false;
}

bool Process::Read(LPCVOID addr, void* buf, size_t sz) const {
    if (!handle_) return false;
    SIZE_T bytesRead;
    // ReadProcessMemory copies data from the target process's memory into our buffer.
    // It's like peeking into someone else's notebook!
    return ReadProcessMemory(handle_, addr, buf, sz, &bytesRead) && bytesRead == sz;
}

bool Process::Write(LPVOID addr, const void* buf, size_t sz) {
    if (!handle_) return false;
    SIZE_T bytesWritten;
    // WriteProcessMemory changes data in the target process. 
    // This is how we change health, ammo, or position!
    return WriteProcessMemory(handle_, addr, buf, sz, &bytesWritten) && bytesWritten == sz;
}

} // namespace GameTrainer

// --- CPP Interface Implementation ---

// TEACHER NOTE: ACROMYM CHEAT SHEET!
// ------------------------------------------------------------------
// gt_:     Stands for "GameTrainer". We use it to name our functions 
//          so they don't crash into other functions with the same name.
//
// DWORD:   "Double Word". It's just a 32-bit positive whole number.
// HANDLE:  Think of this like a "Ticket". Windows gives us this ticket
//          so we can access the game process later.
// LPCVOID: "Long Pointer to Constant Void". Scary name, simple meaning:
//          It's just a "Memory Address" (like a house address).
// ------------------------------------------------------------------

bool gt_find_process_id(const char* name, DWORD* out_pid) {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return false;

    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(pe);

    if (Process32First(hSnap, &pe)) {
        do {
            if (strcmp(pe.szExeFile, name) == 0) {
                *out_pid = pe.th32ProcessID;
                CloseHandle(hSnap);
                return true;
            }
        } while (Process32Next(hSnap, &pe));
    }

    CloseHandle(hSnap);
    return false;
}

bool gt_open_process(DWORD pid, gt_process_t* out) {
    if (!out) return false;
    
    // We can use the C++ class internally to validate, but since the C struct needs the raw handle,
    // we'll just do the raw WinAPI calls here to avoid ownership confusion (who owns the handle? the struct or the class?).
    // For a pure C API wrapper, it's often safer to keep it simple unless we wrap the C++ object in a void*.
    
    out->handle = OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION, FALSE, pid);
    if (!out->handle) return false;
    
    out->pid = pid;
    gt_is_process_64bit(out->handle, &out->is64bit);
    return true;
}

void gt_close_process(gt_process_t* proc) {
    if (proc && proc->handle) {
        CloseHandle(proc->handle);
        proc->handle = NULL;
        proc->pid = 0;
    }
}

bool gt_is_process_64bit(HANDLE hProc, bool* out) {
    if (!out) return false;
    BOOL isWow64 = FALSE;
    if (!IsWow64Process(hProc, &isWow64)) return false;
    *out = !isWow64; 
    return true;
}

bool gt_read(HANDLE h, LPCVOID addr, void* buf, size_t sz) {
    SIZE_T bytesRead;
    return ReadProcessMemory(h, addr, buf, sz, &bytesRead) && bytesRead == sz;
}

bool gt_write(HANDLE h, LPVOID addr, const void* buf, size_t sz) {
    SIZE_T bytesWritten;
    return WriteProcessMemory(h, addr, buf, sz, &bytesWritten) && bytesWritten == sz;
}
