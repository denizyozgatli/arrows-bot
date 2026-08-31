# Arrow Solver — Claude Code Instructions

@AGENTS.md

## Project Context

Arrow Solver is a prototype Android/ADB automation and computer-vision project.

Read `PROJECT.md` for the complete project definition.

Read `docs/roadmap.md` before making architectural changes.

The current implementation is **not** a persistent multi-viewport solver. In particular:

- `vision/detector.py` uses handcrafted template matching.
- `vision/mapper.py` is empty.
- `solver/navigator.py` is empty.
- `solver/graph.py` performs local screen-space ray checks; it is not a persistent graph.
- `executor/bot.py` repeatedly captures the current viewport and taps one locally selected arrow.
- A persistent world model, robust exploration system, and state-transition verification are not yet implemented.

Do not assume planned architecture is existing functionality.

## Working Rules

For non-trivial work:

1. Inspect the repository and relevant implementation first.
2. Identify the actual failure mode.
3. Form a hypothesis.
4. Prefer the smallest useful experiment or implementation.
5. Run appropriate verification.
6. Report verified results and remaining uncertainty.

Hard and Super Hard levels may require scrolling. Never assume the current viewport contains the entire puzzle.

Treat unseen regions as unknown, not empty.

Do not introduce deep learning simply because the current system fails. First establish whether perception is actually the bottleneck.

Do not invent tests, benchmark results, file contents, APIs, or command output.

Keep `CLAUDE.md` concise. Put durable project facts in `PROJECT.md`, agent behavior in `AGENTS.md`, experiments in `docs/experiments/`, decisions in `docs/decisions/`, and the active plan in `docs/roadmap.md`.
