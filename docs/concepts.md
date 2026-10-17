# Concepts

> **Covers:** the ideas you need to understand GameTrainer, in plain English.
> **Status:** current. **Last verified:** 2026-10-17.
> **Authority:** this file explains *how things work*. Word definitions live in [`glossary.md`](glossary.md). How the code is organised lives in [`architecture.md`](architecture.md).

## 1. The big idea

GameTrainer teaches a computer to play games by **trial and error**. That's called **reinforcement learning (RL)**. We don't write the learning part ourselves; we borrow it. *Why:* learning code is easy to get subtly wrong. We build the **plumbing** that lets any game plug into any learner.

Three parts:

```
   AI (the player)                     Ground (the game)
 ┌──────────────────────┐          ┌──────────────────┐
 │ Eyes → Brain → Hands │ ──act──▶ │  rules + score   │
 │   ▲                  │ ◀─see─── │                  │
 └───┼──────────────────┘ ◀─score─ └──────────────────┘
     └──────── all through the Link (Gymnasium) ───────┘
```

- **Ground**: the game. It shows what's happening and gives a score.
- **AI**: the player. **Eyes** see, the **Brain** decides, the **Hands** press keys.
- **Link**: the standard plug between them. We use a library called **Gymnasium**.

## 2. The loop

Everything is one loop, repeated thousands of times:

```
observe → act → reward → repeat
```

1. **Observe**: the game says what's on screen.
2. **Act**: the brain picks a move.
3. **Reward**: the game gives a score for that move.

## 3. The contract: `reset()` and `step()`

A **contract** is a promise about how code behaves. Gymnasium's contract is two methods. Every game must have both:

```python
observation, info = env.reset()       # start a new game
observation, reward, terminated, truncated, info = env.step(action)   # make one move
```

*Why it matters:* if a game keeps this promise, **any** learner can play it. That swappability is the whole project.

### `terminated` vs `truncated`

There are two different ways for a game to end, and mixing them up quietly breaks learning.

| | Means | Example | Future reward |
| :--- | :--- | :--- | :--- |
| `terminated` | The game's rules ended it | reached the goal, hit a mine | zero: the game is really over |
| `truncated` | We cut it short | ran out of moves | not zero: it *could* have kept going |

*Why:* if a timeout is marked `terminated`, the learner thinks that square is a dead end and learns to avoid it.

## 4. The brain: PPO

**PPO** (Proximal Policy Optimization) is the learning method we borrow from the library **stable-baselines3**. *Why PPO:* it's the common, stable default for this kind of problem.

Inside, it has two parts:

- **Actor**: picks a move. ("Press right.")
- **Critic**: guesses how good the current spot is. ("This is worth about +0.75.")

After a move, PPO compares what *happened* to what the critic *expected*. That difference is the **advantage**. Better than expected → do it more. Worse → do it less.

**"Proximal"** means "stay close". PPO limits how much it changes per update (about 20%). *Why:* big jumps can wreck what it already learned.

## 5. The eyes

There are two different sets of eyes, for two different jobs.

### Eyes for GridWorld pictures: a Vision Transformer (M3)

A **Vision Transformer (ViT)** is a neural network that reads images. It cuts the picture into 196 small squares (**patches**). Then every patch can compare itself to every other patch right away. That's called **self-attention**. *Why a ViT:* in games, things far apart on screen (a health bar, an enemy) often matter together.

We use a small one (**ViT-Tiny**), **pretrained** on 1.2 million photos (ImageNet), and **frozen**, meaning it doesn't learn any further. *Why frozen:* training 5.7 million numbers on a CPU would take days, and the pretrained ones already know edges and shapes. It turns each picture into 192 numbers for PPO.

### Eyes for Minesweeper: a board reader (M5)

`read_board()` looks at a screenshot and returns an 8×8 grid of numbers. It doesn't learn anything; it follows measured rules:

1. **Find the board**: the biggest dark square in the picture.
2. **Read each cell**: check the background colour (hidden or revealed), then the glyph colour (which number, or a flag).
3. **If unsure, stop with an error.** *Why:* a wrong guess would quietly feed the learner a wrong board.

## 6. The hands

The hands send **real key presses** to a real game window.

- **Windows:** `SendInput`. It puts a key event on the same queue a real keyboard uses.
- **macOS:** `CGEventPost` (Quartz). Same idea, Apple's version.

One safety rule: **keys go to whichever window is in front.** So the hands check the game is in front before every key, and refuse otherwise. *Why:* otherwise our moves could get typed into your code editor.

For games that don't need real keys (CartPole, GridWorld), we use `NullInput`: hands that do nothing.

## 7. Screen capture

`mss` takes a screenshot of just the game window. Two traps it had to handle, each found by measuring:

- **High-DPI screens** (where Windows scales everything up): Windows reports scaled positions, but screenshots use real pixels. We switch scaling off at startup.
- **Invisible borders**: Windows counts an invisible 8 px border around each window. We ask for the *visible* edges instead.

## 8. Tests vs experiments

| | Test | Experiment |
| :--- | :--- | :--- |
| Asks | "Does the code keep its promises?" | "Did the agent actually learn?" |
| Speed | seconds | minutes |
| Same answer every time? | yes | no (training is random) |
| Run by | `pytest`, on every change | a milestone script, by hand |

*Why keep them apart:* a slow, flaky test gets skipped, and a skipped test protects nothing.
