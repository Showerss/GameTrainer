# GameTrainer - Product Requirements Document (PRD)

## 1. Executive Summary
GameTrainer is a local, vision-based Reinforcement Learning (RL) system designed to train autonomous agents to play games through visual perception and trial-and-error learning. Unlike traditional bots that rely on hardcoded rules or memory reading, GameTrainer perceives the game world like a human: via screen pixels.

The system is currently optimized for Stardew Valley but is designed to be a game-agnostic framework.

## 2. Technical Philosophy & "The Pivot"
In early 2026, the project pivoted away from manual pixel-detection and rule-based logic toward a modern deep learning approach:
- **No Memory Reading:** No process injection or memory scanning.
- **Vision Transformers (ViT):** Utilizing global attention to understand spatial relationships (e.g., connecting a health bar in the corner to a monster in the center).
- **Local Sovereignty:** All training and inference happen locally on the user's GPU (optimized for 9070xt class hardware) to avoid API costs and data privacy issues.

## 3. System Architecture

### 3.1 The Perception Pipeline (The Eyes)
- **Model:** Vision Transformer (ViT) via `timm` library.
- **Input:** 224x224 RGB images.
- **Pre-training:** Leverages ImageNet weights for transfer learning to jumpstart "shape" and "color" recognition.
- **Resolution Strategy:** The 1080p game window is downsampled. While fine text is sacrificed, the agent focuses on global patterns, movement, and color-coded gauges (health/energy).

### 3.2 The RL Engine (The Brain)
- **Framework:** `gymnasium` and `stable-baselines3`.
- **Algorithm:** Proximal Policy Optimization (PPO).
- **Observation Space:** 224x224x3 visual frames.
- **Action Space:** Discrete/MultiDiscrete mappings for movement (WASD), tool usage, and menu navigation.

### 3.3 The Input System (The Hands)
- **Mechanism:** Custom C++ `SendInput` wrapper.
- **Precision:** Microsecond-level timing accuracy.
- **Anti-Detection:** Humanized input patterns with random jitter and normalized distributions for delays.

## 4. Hardware & Resource Usage
| Phase | Hardware Target | API Cost | Latency |
| :--- | :--- | :--- | :--- |
| **Training** | GPU (9070xt) - Heavy | $0 (Local) | N/A |
| **Inference** | GPU - Light/Moderate | $0 | < 30ms |

## 5. Game Profiles & Scalability
The engine remains game-agnostic by using **Profiles**:
- `profile.yaml`: Input mappings and settings.
- `checkpoints/`: Saved `.zip` RL models.
- `templates/`: Optional UI elements for state-specific rewards.
- `knowledge/`: Optional external data (e.g., crop growth times).

## 6. Safety & Ethical Boundaries
- **Scope:** Intended for local, single-player games only.
- **User Override:** Automatic pause-on-user-input (mouse/keyboard movement).
- **Window Isolation:** Logic ensures the agent only interacts with the target game window.

## 7. Educational Focus
This project serves as a teaching tool for:
- **Architecture:** Multi-language systems (Python/C++).
- **Deep Learning:** Vision Transformers in real-world application.
- **System Design:** Performance optimization and low-latency pipelines.
