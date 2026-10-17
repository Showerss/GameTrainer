# Glossary

> **Covers:** every project and RL word, in one sentence each.
> **Status:** current. **Last verified:** 2026-10-17.
> **Authority:** the only glossary in the repo. Ideas are explained in [`concepts.md`](concepts.md).

## Project words

| Word | Meaning |
| :--- | :--- |
| **Ground** | The game. It shows what's happening and gives the score. |
| **AI** | The player: eyes + brain + hands. |
| **Link** | The standard plug between game and player (Gymnasium). |
| **Eyes** | The part that turns pixels into something the brain can use. |
| **Brain** | The part that decides the move (PPO). |
| **Hands** | The part that presses the keys. |
| **Profile** | A `.yaml` text file that names a game and its settings. |
| **Brick** | One small, finished step of work. |
| **Milestone (M0–M6)** | A bigger goal made of bricks, with a clear "done when". |
| **Referee** | Code that measures the baseline and says PASS or FAIL. |
| **Track A / B** | Today's step-by-step path (A) vs. the retired Stardew-first attempt (B). |

## Reinforcement learning words

| Word | Meaning |
| :--- | :--- |
| **Reinforcement learning (RL)** | Learning by trial and error, guided by a score. |
| **Agent** | The learner that takes actions. |
| **Environment** | The world the agent acts in. In code, an object with `reset()` and `step()`. |
| **Observation** | What the agent can see right now. |
| **Action** | One move the agent can make. |
| **Reward** | The score for one move. |
| **Episode** | One full game, from `reset()` until it ends. |
| **Policy** | The agent's habit: "when I see this, I do that." |
| **Baseline** | What a random player scores. You must beat it. |
| **Greedy evaluation** | Testing the agent with no random moves mixed in. |
| **terminated** | The game's rules ended the episode (goal reached, mine hit). |
| **truncated** | We cut the episode short (out of moves). |
| **Discount factor (γ, gamma)** | How much future rewards count compared with rewards now. |
| **PPO** | The learning method we borrow; stable and widely used. |
| **Actor / Critic** | The two halves of PPO: one picks moves, one judges positions. |
| **Advantage** | How much better a move went than the critic expected. |
| **Seed** | A number that fixes the randomness, so a run can be repeated exactly. |

## Software words

| Word | Meaning |
| :--- | :--- |
| **Contract** | A promise about how code behaves (here: `reset()` and `step()`). |
| **Interface** | The list of methods a class promises to have. |
| **Abstract class** | A parent class that can't be used by itself; children must fill in its blanks. |
| **Wrapper** | An object that sits around another one and changes one thing. |
| **Factory** | A function whose job is building the right object. |
| **Dependency injection** | Handing an object what it needs, instead of it building its own. |
| **Composition** | An object builds its own part and controls its life (UML `*--`). |
| **Aggregation** | An object is handed a part from outside (UML `o--`). |
| **Negative control** | A test where nothing should happen. It proves your cause was real. |
| **Fixture** | Saved test input, like a real screenshot. |
| **ADR** | Architecture Decision Record: a short note on one big decision and why. |

## Vision words

| Word | Meaning |
| :--- | :--- |
| **ViT (Vision Transformer)** | A neural network that reads images as a grid of patches. |
| **Patch** | One small square of the image (16×16 pixels). |
| **Self-attention** | Every patch compares itself with every other patch. |
| **Pretrained** | Already trained on other data (here: 1.2M photos). |
| **Frozen** | Not trained any further. |
| **DPI scaling** | Windows enlarging things on high-resolution screens. |
