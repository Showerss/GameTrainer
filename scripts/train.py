"""
Training Script for Stardew Valley RL Agent (ViT Edition)

This script uses a Vision Transformer (ViT) for visual processing instead of CNN.

Usage:
    python scripts/train.py              # Default: ViT-Small
    python scripts/train.py small        # ViT-Small (22M params, recommended)
    python scripts/train.py tiny         # ViT-Tiny (5.7M params, fast experiments)
    python scripts/train.py base         # ViT-Base (86M params, maximum power)

    python scripts/train.py small --freeze    # Freeze ViT backbone (faster training)
    python scripts/train.py small --steps 50000  # Custom timestep count

Teacher Note: Why ViT over CNN?
===============================
CNNs process locally - a convolution filter only sees a small region.
Global understanding requires many layers of pooling.

ViT processes globally from layer 1 - any patch can attend to any other patch.
This is perfect for games where UI elements in corners relate to each other:
aawwssaawwddaaaawwsswwddaasswwddwwaa- Health bar (corner) + food in inventory (bottom) = "should I eat?"
- Time display (top) + energy level (side) = "should I go to bed?"

The pretrained ImageNet weights give us a huge head start - the model
already knows about edges, shapes, colors, and spatial patterns.
"""

import os
import sys
import time
import argparse
import subprocess
import numpy as np

# Add project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

# Verify we can find the gametrainer package
if not os.path.exists(os.path.join(_project_root, "src", "gametrainer")):
    print(f"[!!] ERROR: Cannot find src/gametrainer package!")
    print(f"     Current working directory: {os.getcwd()}")
  ww  print(f"     Script location: {os.path.abspath(__file__)}")
    print(f"     Project root: {_project_root}")
    print(f"     Please run from project root: python scripts/train.py small")
    sys.exit(1)
wwdd

# =============================================================================
# DEPENDENCY MANAGEMENT
# =============================================================================

def ensure_package(install_name: str, import_name: str = None) -> bool:
    """
    Check if a package is installed, and install it if not.

    Args:
        install_name: Package name for pip (e.g., 'timm')
        import_name: Module name for import (e.g., 'timm'). Defaults to install_name.

    Returns:
        True if package is available (installed or was installed), False on failure.
    """
    if import_name is None:
        import_name = install_name

    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"[!] {install_name} not found. Installing...")
        print(f"    This may take a few minutes (especially for stable-baselines3)...")
        print(f"    Installing {install_name}...")
        try:
            # Show output in real-time so user can see progress
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", install_name],
                stdout=None,  # Show stdout
                stderr=subprocess.STDOUT  # Merge stderr into stdout
            )
            print(f"[OK] {install_name} installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!!] Failed to install {install_name}: {e}")
            print(f"    Try manually: pip install {install_name}")
            return False


def check_all_dependencies() -> bool:
    """
    Ensure all required dependencies are installed.

    Returns:
        True if all dependencies are available, False otherwise.
    """
    print("Checking dependencies...")
    print("-" * 40)

    all_ok = True

    # Core RL dependencies
    dependencies = [
        ("torch", "torch"),
        ("gymnasium", "gymnasium"),
        ("stable-baselines3", "stable_baselines3"),
        ("timm", "timm"),  # For ViT models
        ("mss", "mss"),  # For screen capture
        ("opencv-python", "cv2"),  # For image processing
        ("tensorboard", "tensorboard"),  # For training visualization
        ("tqdm", "tqdm"),  # For progress bars
        ("rich", "rich"),  # For nice formatting
        ("pywin32", "win32gui"),  # For window management
    ]

    for install_name, import_name in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"  [OK] {install_name} ({version})")
        except ImportError:
            if ensure_package(install_name, import_name):
                print(f"  [OK] {install_name} (just installed)")
            else:
                print(f"  [!!] {install_name} FAILED")
                all_ok = False

    print("-" * 40)
    return all_ok


# =============================================================================
# IMPORT AFTER DEPENDENCIES ARE CHECKED
# =============================================================================

def do_imports():
    """Import training modules after dependencies are verified."""
    global PPO, DummyVecEnv, CheckpointCallback, BaseCallback
    global StardewViTEnv, ViTFeaturesExtractor, ViTSmallFeaturesExtractor, ViTTinyFeaturesExtractor

    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback

    from src.gametrainer.env_vit import StardewViTEnv
    from src.gametrainer.vit_extractor import (
        ViTFeaturesExtractor,
        ViTSmallFeaturesExtractor,
        ViTTinyFeaturesExtractor
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_TIMESTEPS = 100_000
CHECKPOINT_FREQ = 10_000
MODEL_DIR = "models/ppo_stardew_vit"
LOG_DIR = "logs/vit"


# =============================================================================
# ACTION LOGGING CALLBACK
# =============================================================================

class ActionLoggingCallback:
    """Placeholder - will be defined after imports."""
    pass


def create_action_logging_callback():
    """Create the callback class after imports are done."""

    class ActionLoggingCallback(BaseCallback):
        """
        Callback to log action distribution and verify agent is exploring.
        """
        ACTION_NAMES = [
            "NO-OP", "UP(W)", "DOWN(S)", "LEFT(A)", "RIGHT(D)",
            "LEFT_CLICK", "RIGHT_CLICK",
            "MOUSE_UP", "MOUSE_DOWN", "MOUSE_LEFT", "MOUSE_RIGHT",
            "ESC"
        ]

        def __init__(self, log_freq: int = 1000, verbose: int = 1):
            super().__init__(verbose)
            self.log_freq = log_freq
            self.action_counts = np.zeros(len(self.ACTION_NAMES))

        def _on_step(self) -> bool:
            actions = self.locals.get("actions")
            if actions is not None:
                if isinstance(actions, np.ndarray):
                    if actions.ndim == 0:
                        action = int(actions.item())
                        self.action_counts[action] += 1
                    else:
                        for action in actions.flatten():
                            self.action_counts[int(action)] += 1

            if self.n_calls % self.log_freq == 0:
                total = self.action_counts.sum()
                if total > 0:
                    percentages = (self.action_counts / total * 100).round(1)
                    print(f"\n[Step {self.n_calls}] Action distribution:")
                    for name, count, pct in zip(self.ACTION_NAMES, self.action_counts, percentages):
                        if count > 0:
                            bar = "#" * int(pct / 5)
                            print(f"  {name:12s}: {int(count):5d} ({pct:5.1f}%) {bar}")
                    print()

            return True

    return ActionLoggingCallback


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train a ViT-based RL agent for Stardew Valley",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/train.py              # Default: ViT-Small
  python scripts/train.py small        # ViT-Small (recommended)
  python scripts/train.py tiny         # ViT-Tiny (fast, less VRAM)
  python scripts/train.py base         # ViT-Base (powerful, needs 12GB+ VRAM)

  python scripts/train.py small --freeze       # Freeze backbone (faster)
  python scripts/train.py small --steps 50000  # Train for 50k steps

ViT Sizes:
  tiny   5.7M params, ~3GB VRAM  - Fast experiments
  small  22M params,  ~6GB VRAM  - Recommended balance
  base   86M params,  ~12GB VRAM - Maximum capability
        """
    )

    parser.add_argument(
        "size",
        nargs="?",
        default="small",
        choices=["tiny", "small", "base"],
        help="ViT model size (default: small)"
    )

    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Freeze ViT backbone (faster training, less adaptable)"
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_TIMESTEPS,
        help=f"Total training timesteps (default: {DEFAULT_TIMESTEPS:,})"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from latest checkpoint (default: auto-detect)"
    )

    return parser.parse_args()


# =============================================================================
# MAIN TRAINING FUNCTION
# =============================================================================

def main():
    try:
        # Parse command-line arguments
        print("[DEBUG] Starting train.py...")
        args = parse_args()
        print(f"[DEBUG] Parsed arguments: size={args.size}, steps={args.steps}, freeze={args.freeze}")

        print("=" * 60)
        print("GAMETRAINER - ViT EDITION")
        print("=" * 60)
        print()

        # 1. Check and install dependencies
        if not check_all_dependencies():
            print("\n[!!] Some dependencies failed to install.")
            print("     Try manually: pip install -e .[rl]")
            response = input("     Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Exiting...")
                return

        # 2. Import modules now that dependencies are verified
        print("\nLoading modules...")
        try:
            do_imports()
            print("[OK] All modules loaded\n")
        except Exception as e:
            print(f"\n[!!] Failed to import modules: {e}")
            print(f"     Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return
    except Exception as e:
        print(f"\n[!!] Fatal error in main(): {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Check C++ extension
    print("Checking C++ input extension...")
    try:
        import src.gametrainer.clib as clib
        print("  [OK] C++ input extension loaded")
    except ImportError:
        print("  [!!] WARNING: C++ input extension not found!")
        print("       Actions will NOT be sent to the game!")
        print("       Run 'pip install -e .' to build the extension.")
        response = input("       Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # 4. Create directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # 5. Initialize Environment
    print("\nInitializing environment...")
    env = DummyVecEnv([lambda: StardewViTEnv(render_mode='rgb_array')])

    # 6. Select ViT variant based on argument
    print(f"\n{'='*60}")
    print(f"CONFIGURATION")
    print(f"{'='*60}")
    print(f"  Model Size:     {args.size.upper()}")
    print(f"  Freeze Backbone: {args.freeze}")
    print(f"  Training Steps: {args.steps:,}")

    if args.size == "tiny":
        features_extractor_class = ViTTinyFeaturesExtractor
        features_dim = 192
        print(f"\n  ViT-Tiny: 5.7M params, 192-dim features")
        print(f"  Best for: Quick experiments, limited VRAM (~3GB)")
    elif args.size == "small":
        features_extractor_class = ViTSmallFeaturesExtractor
        features_dim = 384
        print(f"\n  ViT-Small: 22M params, 384-dim features")
        print(f"  Best for: Good balance of speed and capability (~6GB)")
    else:  # base
        features_extractor_class = ViTFeaturesExtractor
        features_dim = 768
        print(f"\n  ViT-Base: 86M params, 768-dim features")
        print(f"  Best for: Maximum capability (~12GB VRAM)")

    print(f"{'='*60}\n")

    # 7. Policy kwargs
    policy_kwargs = dict(
        features_extractor_class=features_extractor_class,
        features_extractor_kwargs=dict(
            pretrained=True,
            freeze_backbone=args.freeze,
        ),
        net_arch=dict(
            pi=[256, 128],
            vf=[256, 128],
        ),
    )

    # 8. Load existing model or create new one
    model = None

    model_paths = [
        f"{MODEL_DIR}/final_model.zip",
        f"{MODEL_DIR}/interrupted_model.zip",
    ]

    if os.path.exists(MODEL_DIR):
        checkpoints = [f for f in os.listdir(MODEL_DIR)
                      if f.startswith("stardew_vit_") and f.endswith(".zip")]
        if checkpoints:
            checkpoints.sort(
                key=lambda x: int(x.replace("stardew_vit_", "").replace("_steps.zip", "")),
                reverse=True
            )
            model_paths.append(os.path.join(MODEL_DIR, checkpoints[0]))

    for path in model_paths:
        if os.path.exists(path):
            print(f"Found existing model: {path}")
            print("  Loading and resuming training...")
            try:
                model = PPO.load(
                    path,
                    env=env,
                    device="auto",
                    tensorboard_log=LOG_DIR,
                )
                print(f"  [OK] Model loaded successfully!")
                break
            except Exception as e:
                print(f"  [!!] Failed to load: {e}")
                print("       Starting fresh (architecture may have changed)...")

    if model is None:
        print("Creating new PPO agent with ViT...")
        model = PPO(
            "CnnPolicy",
            env,
            policy_kwargs=policy_kwargs,
            verbose=1,
            tensorboard_log=LOG_DIR,
            device="auto",
            learning_rate=1e-4,
            n_steps=1024,
            batch_size=32,
            n_epochs=5,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
        )

    # 9. Print model summary
    print(f"\n{'='*60}")
    print("MODEL SUMMARY")
    print('='*60)
    total_params = sum(p.numel() for p in model.policy.parameters())
    trainable_params = sum(p.numel() for p in model.policy.parameters() if p.requires_grad)
    print(f"  Total parameters:     {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    print(f"  Frozen parameters:    {total_params - trainable_params:,}")
    print('='*60)

    # 10. Setup callbacks
    from stable_baselines3.common.callbacks import CallbackList

    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=MODEL_DIR,
        name_prefix="stardew_vit"
    )

    ActionLoggingCallbackClass = create_action_logging_callback()
    action_logger = ActionLoggingCallbackClass(log_freq=1000)

    callback_list = CallbackList([checkpoint_callback, action_logger])

    # 11. Start training
    print(f"\nStarting training for {args.steps:,} timesteps...")
    print("Switch to the Stardew Valley window NOW!")
    print("=" * 60)

    for i in range(5, 0, -1):
        print(f"  Starting in {i}...")
        time.sleep(1)

    print("\n[TRAINING STARTED]\n")

    try:
        # Check if progress bar is available
        try:
            import tqdm
            import rich
            progress_bar = True
        except ImportError:
            progress_bar = False

        model.learn(
            total_timesteps=args.steps,
            callback=callback_list,
            progress_bar=progress_bar
        )

        print("\n" + "=" * 60)
        print("TRAINING COMPLETE!")
        print("=" * 60)
        model.save(f"{MODEL_DIR}/final_model")
        print(f"Model saved to: {MODEL_DIR}/final_model.zip")

    except KeyboardInterrupt:
        print("\n\nTraining interrupted. Saving model...")
        model.save(f"{MODEL_DIR}/interrupted_model")
        print(f"Model saved to: {MODEL_DIR}/interrupted_model.zip")

    finally:
        env.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!!] Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
