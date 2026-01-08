# GameTrainer Design Document (RL Edition)

> **Scope note (ethics & legality):** This project is intended for **local,
> single‑player games** (e.g., Stardew Valley) and **offline**
> experimentation on games **you own and control**.

---

## 1. Overview

### 1.1 Purpose

GameTrainer is a **vision-based** Reinforcement Learning (RL) system that trains an autonomous agent to play games. Unlike traditional bots that use hardcoded rules, GameTrainer uses a **Vision Transformer (ViT)** to "see" the screen and a **Proximal Policy Optimization (PPO)** algorithm to learn optimal strategies through trial and error.

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│  Screen Capture │ ──► │  RL Agent (PPO/ViT on GPU)   │ ──► │ Input Simulate  │
│   (mss/opencv)  │     │   (SB3 + timm ViT)           │     │   (SendInput)   │
└─────────────────┘     └──────────────────────────────┘     └─────────────────┘
```

### 1.2 Core Philosophy

- **Pixels-to-Actions:** The agent learns directly from visual input, just like a human. No memory reading or process injection.
- **Global Attention:** Using Vision Transformers (ViT) allows the agent to relate distant UI elements (like health bars and inventory) instantly.
- **Local & Private:** All training and inference happens locally on the user's GPU (optimized for high-end hardware like the 9070xt).

---

## 2. Architecture

### 2.1 The Perception System (ViT)
Instead of standard CNNs, we use a **Vision Transformer**. 
- **Resolution:** 224x224 RGB.
- **Feature Extraction:** Leveraging pre-trained ImageNet weights via the `timm` library to jump-start the agent's understanding of shapes and colors.
- **Global Context:** Self-attention layers allow the model to process the entire screen state simultaneously.

### 2.2 The Environment (Gymnasium)
The game is wrapped in a standard `gymnasium` environment:
- **Observation Space:** 224x224x3 (RGB) image.
- **Action Space:** Discrete actions (Move WASD, Mouse clicks, Mouse movement, ESC).
- **Reward Function:** A multi-component signal based on survival, energy levels, and movement detection.

### 2.3 Training Pipeline (Stable-Baselines3)
- **Algorithm:** PPO (Proximal Policy Optimization).
- **Update Cycle:** Collects 1024 steps of gameplay, then pauses to update the neural network weights on the GPU.
- **Hardware Acceleration:** Heavily utilizes CUDA for both the Transformer backbone and the policy optimization.

---

## 3. Data Flow

1. **Capture:** `mss` grabs the game window at high frequency.
2. **Preprocess:** Frame is resized to 224x224 and normalized for the ViT.
3. **Inference:** The ViT extracts a feature vector (e.g., 384-dim for ViT-Small) which is fed into the PPO policy.
4. **Action:** The agent selects an action, which is sent to the game via a custom C++ `SendInput` wrapper.
5. **Reward:** The environment evaluates the resulting frame to see if the action was "good" (e.g., did the character move? did energy drop?).

---

## 4. Safety & Limits

- **User Override:** The system detects manual mouse/keyboard movement to pause automation.
- **Window Locking:** Robust detection logic ensures the bot only "sees" and "clicks" on the intended game window, ignoring tooltips and overlays.
- **Rate Limiting:** Actions are throttled to human-like speeds to prevent game engine issues.

---

*Document version: 4.0 (RL + Vision Transformer Architecture)*
*Last updated: January 2026*