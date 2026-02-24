"""
Transfer Learning Utilities

This script shows how to:
1. Extract and save just the CNN (feature extractor) from a trained model
2. Load a pre-trained CNN into a new model
3. Fine-tune vs freeze layers

Teacher Note: Transfer learning lets you reuse what the model learned about
"seeing" (edges, shapes, UI patterns) while retraining what it learned about
"doing" (which actions to take).
"""

import os
import sys
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from src.gametrainer.env_vit import StardewViTEnv

# Note: Script describes CNN transfer learning; same ideas apply to ViT (freeze backbone vs fine-tune).


def inspect_model(model_path: str):
    """
    Show what's inside a trained model - helps understand what can be transferred.
    """
    print(f"\n{'='*60}")
    print(f"INSPECTING MODEL: {model_path}")
    print('='*60)

    model = PPO.load(model_path)
    policy = model.policy

    print("\n[POLICY NETWORK STRUCTURE]")
    print("-" * 40)

    # The CNN feature extractor
    print("\n1. FEATURE EXTRACTOR (CNN) - TRANSFERABLE!")
    print("   These layers learn to 'see' - edges, shapes, patterns")
    if hasattr(policy, 'features_extractor'):
        for name, param in policy.features_extractor.named_parameters():
            print(f"   • {name}: {list(param.shape)}")

    # The MLP that processes features
    print("\n2. MLP EXTRACTOR - PARTIALLY TRANSFERABLE")
    print("   Combines visual features into abstract representations")
    if hasattr(policy, 'mlp_extractor'):
        for name, param in policy.mlp_extractor.named_parameters():
            print(f"   • {name}: {list(param.shape)}")

    # The action and value heads
    print("\n3. ACTION NET - TASK SPECIFIC (retrain this)")
    print("   Decides which action to take")
    if hasattr(policy, 'action_net'):
        for name, param in policy.action_net.named_parameters():
            print(f"   • {name}: {list(param.shape)}")

    print("\n4. VALUE NET - TASK SPECIFIC (retrain this)")
    print("   Estimates how good current state is")
    if hasattr(policy, 'value_net'):
        for name, param in policy.value_net.named_parameters():
            print(f"   • {name}: {list(param.shape)}")

    # Count parameters
    total_params = sum(p.numel() for p in policy.parameters())
    cnn_params = sum(p.numel() for p in policy.features_extractor.parameters()) if hasattr(policy, 'features_extractor') else 0

    print(f"\n[PARAMETER COUNTS]")
    print(f"   Total parameters: {total_params:,}")
    print(f"   CNN parameters:   {cnn_params:,} ({100*cnn_params/total_params:.1f}% - reusable!)")
    print(f"   Other parameters: {total_params - cnn_params:,} ({100*(total_params-cnn_params)/total_params:.1f}%)")

    return model


def save_feature_extractor(model_path: str, output_path: str):
    """
    Save ONLY the CNN feature extractor for reuse in other models.

    Teacher Note: The feature extractor is the most valuable part to transfer
    because it learned general visual features (edges, shapes, UI patterns).
    """
    print(f"\nExtracting feature extractor from: {model_path}")

    model = PPO.load(model_path)

    # Get the CNN weights
    cnn_state_dict = model.policy.features_extractor.state_dict()

    # Save just the CNN
    torch.save({
        'cnn_state_dict': cnn_state_dict,
        'obs_shape': (4, 84, 84),  # Our observation shape
        'source_model': model_path,
    }, output_path)

    print(f"Saved CNN feature extractor to: {output_path}")
    print("This can be loaded into new models to give them a 'head start' on vision!")

    return output_path


def create_model_with_pretrained_cnn(cnn_path: str, env, freeze_cnn: bool = True):
    """
    Create a NEW model but load pre-trained CNN weights.

    Args:
        cnn_path: Path to saved CNN weights
        env: The gymnasium environment
        freeze_cnn: If True, CNN won't be updated during training (faster, preserves features)
                   If False, CNN will be fine-tuned (slower, might improve or forget)

    Teacher Note:
    - freeze_cnn=True: Use when new task is similar (same game, different goal)
    - freeze_cnn=False: Use when new task is different (different game)
    """
    print(f"\nCreating model with pre-trained CNN from: {cnn_path}")
    print(f"CNN frozen: {freeze_cnn}")

    # Create fresh model
    model = PPO("CnnPolicy", env, verbose=1)

    # Load pre-trained CNN weights
    checkpoint = torch.load(cnn_path)
    model.policy.features_extractor.load_state_dict(checkpoint['cnn_state_dict'])
    print("Loaded pre-trained CNN weights!")

    if freeze_cnn:
        # Freeze CNN layers - they won't be updated during training
        for param in model.policy.features_extractor.parameters():
            param.requires_grad = False
        print("CNN layers FROZEN - will not be updated during training")
        print("This preserves learned visual features and speeds up training!")
    else:
        print("CNN layers UNFROZEN - will be fine-tuned during training")
        print("This allows the model to adapt visual features but may 'forget' old patterns")

    return model


def compare_before_after(model_path: str, new_task_model_path: str = None):
    """
    Compare what a model learned before and after training on a new task.
    Useful for understanding what transferred.
    """
    print("\n[TRANSFER LEARNING ANALYSIS]")
    print("="*60)

    model_before = PPO.load(model_path)

    if new_task_model_path and os.path.exists(new_task_model_path):
        model_after = PPO.load(new_task_model_path)

        # Compare CNN weights
        cnn_before = model_before.policy.features_extractor.state_dict()
        cnn_after = model_after.policy.features_extractor.state_dict()

        print("\nCNN Layer Changes:")
        for key in cnn_before.keys():
            diff = (cnn_before[key] - cnn_after[key]).abs().mean().item()
            print(f"  {key}: avg change = {diff:.6f}")
    else:
        print("No comparison model provided. Train on a new task first!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transfer Learning Utilities")
    parser.add_argument("command", choices=["inspect", "extract", "info"],
                       help="Command to run")
    parser.add_argument("--model", type=str, default="models/ppo_stardew/final_model.zip",
                       help="Path to model file")
    parser.add_argument("--output", type=str, default="models/pretrained_cnn.pt",
                       help="Output path for extracted CNN")

    args = parser.parse_args()

    if args.command == "inspect":
        inspect_model(args.model)
    elif args.command == "extract":
        save_feature_extractor(args.model, args.output)
    elif args.command == "info":
        print("""
TRANSFER LEARNING GUIDE
=======================

What can be transferred between training runs:

1. CNN FEATURE EXTRACTOR (highly transferable)
   - Learns edges, shapes, textures, UI patterns
   - Works across similar games (2D pixel art games)
   - Save with: python transfer_learning.py extract --model <path>

2. When to use transfer learning:
   - Same game, different task (farming → mining)
   - Similar game (Stardew → other 2D RPG)
   - Want to speed up training

3. When NOT to use transfer learning:
   - Completely different visual style (2D → 3D)
   - Different resolution/aspect ratio
   - Want model to learn from scratch

4. Commands:
   python scripts/transfer_learning.py inspect --model models/ppo_stardew/final_model.zip
   python scripts/transfer_learning.py extract --model models/ppo_stardew/final_model.zip
""")
