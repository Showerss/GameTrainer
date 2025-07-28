#ifndef HOOK_H
#define HOOK_H

#include <Windows.h>
#include <d3d11.h>

// Installs a hook on the Present function of the swap chain.
BOOL InstallPresentHook(void);

// Removes the previously installed Present hook.
void RemovePresentHook(void);

#endif // HOOK_H