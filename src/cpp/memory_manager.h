//
// Created by phill on 7/28/2025.
//

#ifndef MEMORY_MANAGER_H
#define MEMORY_MANAGER_H

#include <windows.h>

#ifdef __cplusplus
    #include <vector>
    #include <string>
#else
    #include <stdbool.h>
#endif

#ifdef _WIN32
  #define GT_EXPORT __declspec(dllexport)
#else
  #define GT_EXPORT
#endif

namespace GameTrainer {

class Process {
public:
    Process();
    ~Process();

    // Delete copy constructor/assignment to prevent double-free of handle
    Process(const Process&) = delete;
    Process& operator=(const Process&) = delete;

    // Allow move
    Process(Process&& other) noexcept;
    Process& operator=(Process&& other) noexcept;

    bool Attach(const std::string& name);
    bool Attach(DWORD pid);
    void Detach();

    bool Read(LPCVOID addr, void* buf, size_t sz) const;
    bool Write(LPVOID addr, const void* buf, size_t sz);
    
    bool Is64Bit() const { return is64bit_; }
    DWORD GetPid() const { return pid_; }
    HANDLE GetHandle() const { return handle_; }

private:
    HANDLE handle_ = nullptr;
    DWORD pid_ = 0;
    bool is64bit_ = false;
};

} // namespace GameTrainer
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    HANDLE handle;
    DWORD pid;
    bool is64bit;
} gt_process_t;

// Process Management
GT_EXPORT bool gt_find_process_id(const char* name, DWORD* out_pid);
GT_EXPORT bool gt_open_process(DWORD pid, gt_process_t* out);
GT_EXPORT void gt_close_process(gt_process_t* proc);
GT_EXPORT bool gt_is_process_64bit(HANDLE hProc, bool* out);

// Memory Access
GT_EXPORT bool gt_read(HANDLE h, LPCVOID addr, void* buf, size_t sz);
GT_EXPORT bool gt_write(HANDLE h, LPVOID addr, const void* buf, size_t sz);

#ifdef __cplusplus
}
#endif
