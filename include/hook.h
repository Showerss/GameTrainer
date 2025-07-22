#ifndef HOOK_H
#define HOOK_H

#include <Windows.h>
#include <dxgi.h>

// Installs the Present hook. Returns TRUE on success.
BOOL InstallPresentHook();

// Restores the original Present pointer.
void RemovePresentHook();

#endif // HOOK_H
