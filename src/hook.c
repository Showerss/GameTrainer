#include "hook.h"
#include <d3d11.h>
#include <stdio.h>

// We'll store the original Present here.
static IDXGISwapChain *g_pSwapChain = NULL;
static void      *g_originalPresent = NULL;

// Our hooked Present signature
typedef HRESULT (STDMETHODCALLTYPE *PresentFn)(
    IDXGISwapChain*, UINT, UINT
);

HRESULT STDMETHODCALLTYPE HookedPresent(
    IDXGISwapChain* This, UINT SyncInterval, UINT Flags
) {
    // <<< your backbuffer capture logic here >>>
    // call the real Present
    return ((PresentFn)g_originalPresent)(
        This, SyncInterval, Flags
    );
}

BOOL InstallPresentHook() {
    // 1) Create a dummy device+swapchain to read the vtable
    DXGI_SWAP_CHAIN_DESC desc = {0};
    desc.BufferCount       = 1;
    desc.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    desc.BufferUsage       = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    desc.OutputWindow      = GetConsoleWindow(); // just placeholder
    desc.SampleDesc.Count  = 1;
    desc.Windowed          = TRUE;

    ID3D11Device        *dev = NULL;
    ID3D11DeviceContext *ctx = NULL;
    if (FAILED(D3D11CreateDeviceAndSwapChain(
            NULL, D3D_DRIVER_TYPE_HARDWARE, NULL, 0,
            NULL, 0, D3D11_SDK_VERSION,
            &desc, &g_pSwapChain, &dev, NULL, &ctx
    ))) {
        return FALSE;
    }

    // 2) Read vtable and save original Present (index 8)
    void **vtable = *(void***)g_pSwapChain;
    g_originalPresent = vtable[8];

    // 3) Patch it to point at our HookedPresent
    DWORD oldProtect;
    VirtualProtect(
        &vtable[8], sizeof(void*),
        PAGE_EXECUTE_READWRITE, &oldProtect
    );
    vtable[8] = HookedPresent;
    VirtualProtect(
        &vtable[8], sizeof(void*),
        oldProtect, &oldProtect
    );

    return TRUE;
}

void RemovePresentHook() {
    if (!g_pSwapChain) return;
    void **vtable = *(void***)g_pSwapChain;
    DWORD oldProtect;
    VirtualProtect(
        &vtable[8], sizeof(void*),
        PAGE_EXECUTE_READWRITE, &oldProtect
    );
    vtable[8] = g_originalPresent;
    VirtualProtect(
        &vtable[8], sizeof(void*),
        oldProtect, &oldProtect
    );
    g_pSwapChain->Release();
}
