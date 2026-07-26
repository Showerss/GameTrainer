# M3 experiments — the evidence behind `M3_Review.md`

These are the throwaway diagnostic scripts written while chasing the M3 blind-agent
bug, kept because a retrospective built only on the final code would show a tidy
success story and miss the interesting part entirely.

They are **evidence, not part of the toolchain.** Nothing in `src/` or `scripts/`
imports them. Run them from the repo root:

```bash
python docs/m3/experiments/blind_control.py
```

## Re-runnable

| script | what it shows |
|---|---|
| `blind_control.py` | An agent that never sees the picture scores **+0.907** — matching the "trained" ViT agent's +0.905. The single most important result of the milestone. |
| `which_task_needs_eyes.py` | Blind vs sighted across four task designs. Proves the corner goal — not the fixed start — is what made the maze blind-solvable. |
| `calibrate_task.py` | Step-budget calibration. Shows why the 100-move budget left the guardrail unable to grade anything, and why 25 was chosen. |

Exact digits shift slightly between runs (episode start squares are random and
unseeded); the conclusions do not. See the reproducibility note in `M3_Review.md`.

## Historical record only — will not reproduce

| script | why not |
|---|---|
| `diagnose_greedy.py` | Analyses the **blind** trained model, printing its action probabilities at each square. |
| `diagnose_features.py` | Traces how much the pixels / ViT features / policy logits vary across positions in that same model. |

Both load `models/ppo_gridworld_vit/final_model.zip`, and that file was
**overwritten by the successful run**. Running them now loads the *sighted* model
and produces unrelated output. Their original outputs are preserved verbatim in
`M3_Review.md` (Act 2) and in `../run-logs/`.

Keeping the blind model would have made these reproducible — worth doing next time
a run produces a surprising failure. `models/` is gitignored, so archiving it
means copying the `.zip` somewhere tracked, or re-training with a fixed seed.
