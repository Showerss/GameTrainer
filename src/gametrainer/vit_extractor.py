"""
Vision Transformer (ViT) Feature Extractor for Stable-Baselines3

This module implements a custom feature extractor that uses a Vision Transformer
instead of a CNN to process game screenshots.

Teacher Note: Why ViT over CNN?
================================
CNNs process images through LOCAL operations (convolutions look at small regions).
Global context only emerges after many layers of pooling shrink the image.

ViT uses ATTENTION - every part of the image can directly "look at" every other
part from the very first layer. This is crucial for games where:
- The health bar (top-right) relates to the food in hotbar (bottom)
- Enemy position (center) relates to the tool equipped (bottom)
- Time of day (corner) affects what actions make sense

Architecture Overview:
======================
┌─────────────────────────────────────────────────────────────────────────┐
│                         VISION TRANSFORMER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT: 224 x 224 x 3 RGB image                                         │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PATCH EMBEDDING                                                  │   │
│  │  - Cut image into 14x14 grid of 16x16 patches (196 patches)      │   │
│  │  - Each patch: 16×16×3 = 768 values → Linear → 768-dim vector    │   │
│  │  - Add learnable position embeddings (which patch is where?)     │   │
│  │  - Add [CLS] token (special token that aggregates all info)      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  TRANSFORMER ENCODER (×12 layers for ViT-Base)                   │   │
│  │                                                                   │   │
│  │  Each layer:                                                      │   │
│  │  1. Multi-Head Self-Attention                                    │   │
│  │     - Each patch creates Query (Q), Key (K), Value (V) vectors   │   │
│  │     - Attention = softmax(Q × K^T / √d) × V                      │   │
│  │     - "Which other patches should I pay attention to?"           │   │
│  │                                                                   │   │
│  │  2. Feed-Forward Network (MLP)                                   │   │
│  │     - Two linear layers with GELU activation                     │   │
│  │     - Processes each patch's gathered information                │   │
│  │                                                                   │   │
│  │  3. Layer Normalization + Residual Connections                   │   │
│  │     - Helps training stability                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  OUTPUT: [CLS] token → 768-dim feature vector                    │   │
│  │  This single vector captures global image understanding          │   │
│  │  → Fed to policy network (actor) and value network (critic)      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Pre-training Advantage:
=======================
We use a ViT pre-trained on ImageNet (1.2M images, 1000 classes).
Even though ImageNet has cats/dogs/cars (not games), the model learned:
- Edge detection (useful for UI borders, character outlines)
- Color patterns (useful for health bars, item highlights)
- Shape recognition (useful for icons, characters)
- Spatial relationships (useful for understanding layouts)

We "fine-tune" this on game images - the model adapts its knowledge to games.
This is MUCH faster than training from scratch.
"""

import torch
import torch.nn as nn
import gymnasium as gym
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class ViTFeaturesExtractor(BaseFeaturesExtractor):
    """
    Custom feature extractor using Vision Transformer.

    This replaces the default CNN in stable-baselines3 policies.

    Teacher Note: BaseFeaturesExtractor is SB3's interface for custom vision.
    We inherit from it and implement our own forward() method.
    The output is a feature vector that gets fed to the policy/value networks.
    """

    def __init__(
        self,
        observation_space: gym.Space,
        features_dim: int = 768,  # ViT-Base outputs 768-dim vectors
        pretrained: bool = True,
        freeze_backbone: bool = False,
        model_name: str = "vit_base_patch16_224"
    ):
        """
        Initialize the ViT feature extractor.

        Args:
            observation_space: Gym observation space (must be image)
            features_dim: Output dimension (768 for ViT-Base, 384 for ViT-Small)
            pretrained: Load ImageNet weights (HIGHLY recommended)
            freeze_backbone: If True, don't update ViT weights during training
                           (faster but less adaptable to games)
            model_name: Which ViT variant to use (see timm for options)

        Teacher Note on freeze_backbone:
        - freeze_backbone=True: ViT stays fixed, only policy network learns
          → Faster training, good if ImageNet features transfer well
        - freeze_backbone=False: ViT adapts to game images
          → Slower but usually better, model learns game-specific features
        """
        # Initialize parent class with output dimension
        super().__init__(observation_space, features_dim)

        # Import timm here to give clear error if not installed
        try:
            import timm
        except ImportError:
            raise ImportError(
                "timm library required for ViT. Install with:\n"
                "  pip install timm\n"
                "Or: pip install -e .[rl]  (if timm is in extras)"
            )

        # Create the Vision Transformer
        # Teacher Note: timm.create_model handles all the complexity
        # - Downloads pre-trained weights automatically
        # - num_classes=0 removes the classification head (we don't need it)
        # - We only want the feature vector, not ImageNet class predictions
        self.vit = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=0,  # Remove classification head, output features only
        )

        # Log what we're using
        print(f"\n{'='*60}")
        print("VISION TRANSFORMER FEATURE EXTRACTOR")
        print('='*60)
        print(f"  Model: {model_name}")
        print(f"  Pretrained: {pretrained}")
        print(f"  Output features: {features_dim}")
        print(f"  Backbone frozen: {freeze_backbone}")

        # Count parameters
        total_params = sum(p.numel() for p in self.vit.parameters())
        print(f"  Total parameters: {total_params:,}")

        if freeze_backbone:
            # Freeze all ViT parameters - they won't be updated during training
            # Teacher Note: This is like "transfer learning light"
            # The ViT acts as a fixed feature extractor
            for param in self.vit.parameters():
                param.requires_grad = False
            trainable = 0
            print(f"  Trainable parameters: 0 (backbone frozen)")
        else:
            trainable = sum(p.numel() for p in self.vit.parameters() if p.requires_grad)
            print(f"  Trainable parameters: {trainable:,}")

        print('='*60 + "\n")

        # Store config for later reference
        self._features_dim = features_dim
        self.freeze_backbone = freeze_backbone

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        """
        Process a batch of images through the ViT.

        Args:
            observations: Tensor of shape (batch, channels, height, width)
                         Values should be in [0, 255] (uint8) or [0, 1] (float)

        Returns:
            features: Tensor of shape (batch, features_dim)
                     This is the [CLS] token output - a global image summary

        Teacher Note: This method is called every time the agent needs to
        "see" the game. The ViT processes the image and outputs a 768-dim
        vector that captures "what's important in this frame."
        """
        # Normalize to [0, 1] if input is uint8 [0, 255]
        # Teacher Note: Neural networks work better with small values
        if observations.dtype == torch.uint8:
            observations = observations.float() / 255.0

        # ImageNet normalization (what the pretrained ViT expects)
        # Teacher Note: The ViT was trained on ImageNet with specific mean/std.
        # We normalize our game images the same way so the learned features apply.
        mean = torch.tensor([0.485, 0.456, 0.406], device=observations.device)
        std = torch.tensor([0.229, 0.224, 0.225], device=observations.device)

        # Reshape for broadcasting: (3,) -> (1, 3, 1, 1)
        mean = mean.view(1, 3, 1, 1)
        std = std.view(1, 3, 1, 1)

        # Apply normalization: (x - mean) / std
        observations = (observations - mean) / std

        # Forward through ViT
        # Output shape: (batch, features_dim) = (batch, 768) for ViT-Base
        features = self.vit(observations)

        return features


class ViTSmallFeaturesExtractor(ViTFeaturesExtractor):
    """
    Smaller, faster ViT variant.

    Use this if ViT-Base is too slow on your hardware.

    Comparison:
    - ViT-Base:  86M params, 768-dim output, ~12GB VRAM for training
    - ViT-Small: 22M params, 384-dim output, ~6GB VRAM for training

    Teacher Note: For most games, ViT-Small is probably sufficient.
    The smaller model trains faster and may even generalize better
    (less prone to overfitting on limited game data).
    """

    def __init__(
        self,
        observation_space: gym.Space,
        pretrained: bool = True,
        freeze_backbone: bool = False,
    ):
        super().__init__(
            observation_space,
            features_dim=384,  # ViT-Small outputs 384-dim
            pretrained=pretrained,
            freeze_backbone=freeze_backbone,
            model_name="vit_small_patch16_224"
        )


class ViTTinyFeaturesExtractor(ViTFeaturesExtractor):
    """
    Tiny ViT - fastest option, good for experimentation.

    - ViT-Tiny: 5.7M params, 192-dim output, ~3GB VRAM

    Teacher Note: Start with this if you want quick iteration.
    Once you have things working, upgrade to Small or Base.
    """

    def __init__(
        self,
        observation_space: gym.Space,
        pretrained: bool = True,
        freeze_backbone: bool = False,
    ):
        super().__init__(
            observation_space,
            features_dim=192,  # ViT-Tiny outputs 192-dim
            pretrained=pretrained,
            freeze_backbone=freeze_backbone,
            model_name="vit_tiny_patch16_224"
        )


# =============================================================================
# ATTENTION VISUALIZATION (Optional but educational!)
# =============================================================================

def get_attention_maps(model: ViTFeaturesExtractor, image: torch.Tensor):
    """
    Extract attention maps to see WHERE the model is looking.

    This is incredibly useful for understanding what the model learned!
    You can visualize which parts of the screen the model pays attention to.

    Args:
        model: Trained ViT feature extractor
        image: Single image tensor (1, 3, 224, 224)

    Returns:
        attention_maps: Tensor of shape (num_heads, 196, 196)
                       Each head's attention from every patch to every patch

    Teacher Note: Attention visualization answers "what is the model looking at?"
    High attention values on the hotbar/health means it learned those matter.
    This is a huge advantage of transformers - interpretability!

    Usage:
        attn = get_attention_maps(model, game_frame)
        # attn[0, patch_idx, :] shows what patch #patch_idx attends to
        # Reshape 196 → 14x14 grid to visualize as heatmap over image
    """
    # This requires hooks into the ViT's attention layers
    # Implementation depends on the specific timm model structure

    attention_maps = []

    def hook_fn(module, input, output):
        # For timm ViT, attention is computed in the Attention module
        # We capture the attention weights after softmax
        if hasattr(module, 'attn_drop'):
            # output is (B, num_heads, N, N) where N = num_patches + 1 (CLS)
            attention_maps.append(output.detach())

    # Register hooks on attention modules
    hooks = []
    for name, module in model.vit.named_modules():
        if 'attn' in name and hasattr(module, 'attn_drop'):
            hook = module.register_forward_hook(hook_fn)
            hooks.append(hook)

    # Forward pass
    with torch.no_grad():
        _ = model(image)

    # Remove hooks
    for hook in hooks:
        hook.remove()

    if attention_maps:
        # Return attention from last layer (most semantic)
        return attention_maps[-1]
    return None
