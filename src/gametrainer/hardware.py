"""
Hardware / accelerator detection utilities.

Goal: make training/play loops "do the right thing" on whatever machine they're
running on, without hard-requiring CUDA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AcceleratorInfo:
    chosen: str
    torch_version: Optional[str]
    cuda_available: bool
    mps_available: bool


def detect_accelerator(prefer_gpu: bool = True) -> AcceleratorInfo:
    """
    Choose the best available torch device.

    Returns a device string compatible with Stable-Baselines3 `device=...`.
    """
    try:
        import torch
    except Exception:
        # If torch isn't importable yet (e.g. before dependency install),
        # default to CPU.
        return AcceleratorInfo(
            chosen="cpu",
            torch_version=None,
            cuda_available=False,
            mps_available=False,
        )

    cuda_available = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    mps_available = bool(
        getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
    )

    if prefer_gpu:
        if cuda_available:
            chosen = "cuda"
        elif mps_available:
            # Apple Silicon GPU path (not CUDA).
            chosen = "mps"
        else:
            chosen = "cpu"
    else:
        chosen = "cpu"

    return AcceleratorInfo(
        chosen=chosen,
        torch_version=getattr(torch, "__version__", None),
        cuda_available=cuda_available,
        mps_available=mps_available,
    )


def print_accelerator_banner(info: AcceleratorInfo) -> None:
    """
    Print a concise accelerator summary for the user.
    """
    print("\n" + "=" * 60)
    print("HARDWARE / ACCELERATOR CHECK")
    print("=" * 60)
    if info.torch_version:
        print(f"  PyTorch:        {info.torch_version}")
    else:
        print("  PyTorch:        (not available yet)")
    print(f"  CUDA available: {info.cuda_available}")
    print(f"  MPS available:  {info.mps_available}")
    print(f"  Using device:   {info.chosen}")
    if info.chosen == "cpu":
        print("  Note: Training on CPU will be very slow for ViT + PPO.")
        print("        If you expected GPU training, check your torch install.")
    print("=" * 60 + "\n")

