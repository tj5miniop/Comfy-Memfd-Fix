import ctypes
import os
import platform

print("\n--- [Memfd-Fix] Checking Python environment for memfd constants and functions ---")

# 1. Inject missing memory file descriptor constants if they are absent
if not hasattr(os, 'MFD_CLOEXEC'):
    print("[Memfd-Fix] os.MFD_CLOEXEC missing. Injecting Linux flags...")
    os.MFD_CLOEXEC = 0x0001
    os.MFD_ALLOW_SEALING = 0x0002
    os.MFD_HUGETLB = 0x0004

    # Inject standard hugepage shift flags just in case PyTorch tries to request them
    os.MFD_HUGE_SHIFT = 26
    os.MFD_HUGE_64KB = 16 << 26
    os.MFD_HUGE_512KB = 19 << 26
    os.MFD_HUGE_2MB = 21 << 26
    os.MFD_HUGE_8MB = 23 << 26
    os.MFD_HUGE_16MB = 24 << 26
    os.MFD_HUGE_256MB = 28 << 26
    os.MFD_HUGE_1GB = 30 << 26
    os.MFD_HUGE_2GB = 31 << 26

# 2. Inject the fallback function if missing
if not hasattr(os, 'memfd_create'):
    print("[Memfd-Fix] os.memfd_create missing. Injecting native Linux kernel bypass...")

    # Resolve correct Linux syscall numbers depending on architecture
    arch = platform.machine().lower()
    if "x86_64" in arch:
        SYS_memfd_create = 319
    elif "aarch64" in arch or "arm64" in arch:
        SYS_memfd_create = 279
    else:
        # Fallback to standard x86_64 if unknown
        SYS_memfd_create = 319

    def fallback_memfd_create(name: str, flags: int = 0) -> int:
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            # Encode name string to C-compatible bytes
            name_bytes = name.encode('utf-8')

            # Trigger the raw system call
            fd = libc.syscall(SYS_memfd_create, name_bytes, flags)

            if fd < 0:
                err_num = ctypes.get_errno()
                raise OSError(err_num, f"memfd_create failed via custom node bypass (errno: {err_num})")
            return fd
        except Exception as e:
            raise OSError(0, f"Critical failure invoking memfd_create via ctypes: {str(e)}")

    os.memfd_create = fallback_memfd_create
    print("[Memfd-Fix] Success: Environment dynamically patched.\n")
else:
    print("[Memfd-Fix] Environment fully supported. No patch required.\n")

# ComfyUI structural hooks required to let the folder load cleanly as a dummy node
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
