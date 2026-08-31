# Arrow Solver — Project Definition

## 1. Project Overview

Arrow Solver is an automation system for solving an arrow-based puzzle game through Android/ADB screen capture, computer vision, puzzle-state reasoning, and automated input.

The current implementation is a prototype and is **not yet a reliable solver for large or multi-viewport levels**.

The long-term goal is to build a closed-loop agent that can:

1. Observe the game.
2. Detect relevant arrows.
3. Maintain state across multiple observations and scroll positions.
4. Determine safe/legal moves.
5. Explore when the available information is insufficient.
6. Execute an action.
7. Verify the resulting state.
8. Repeat until the puzzle is solved or the run must stop safely.

The project must be designed around the fact that Hard and Super Hard levels may not fit inside a single viewport.

---

## 2. Current Repository Reality

The repository at the time this document was written contains the following relevant implementation:

```text
src/arrows_bot/
├── adb/
│   ├── capture.py
│   ├── connection.py
│   └── input.py
├── executor/
│   └── bot.py
├── solver/
│   ├── graph.py
│   └── navigator.py
├── vision/
│   ├── detector.py
│   └── mapper.py
├── config.py
└── main.py
```

Current implementation status:

| Component | Current state |
|---|---|
| ADB connection | Implemented |
| Screenshot capture | Implemented |
| Tap/swipe input | Implemented |
| Zoom-out helper | Implemented but not part of a robust automatic exploration system |
| Arrow detection | Implemented with handcrafted template matching |
| Arrow mapping | Empty |
| Navigation | Empty |
| Solver | Implemented as a screen-space ray scan, not a persistent graph |
| Executor | Implemented as a reactive one-arrow-at-a-time loop |
| Persistent world state | Not implemented |
| Multi-viewport reconstruction | Not implemented |
| Action verification | Not implemented as a robust state-transition system |
| Automated exploration | Not implemented |
| Evaluation/benchmark harness | Not implemented |

The existing `ARCHITECTURE.md` describes concepts that are not fully implemented in the current source tree. Treat actual source code as the implementation source of truth unless a documented architectural decision explicitly changes it.

---

## 3. Current Implementation

### 3.1 Perception

`vision/detector.py` currently:

- creates four synthetic 23×23 arrow templates
- rotates the template for UP/DOWN/LEFT/RIGHT
- thresholds bright pixels using fixed BGR thresholds
- removes approximately the top 11% and bottom 11% of the screen
- uses `cv2.matchTemplate`
- tests scales `0.6`, `0.8`, and `1.0`
- accepts matches around a fixed threshold
- performs simple proximity-based duplicate suppression

This is a useful prototype baseline, but it is not a robust general-purpose arrow detector.

Known risks include:

- fixed visual assumptions
- sensitivity to scale and rendering changes
- false positives from visually similar shapes
- missed arrows with unusual scale/appearance
- weak handling of partial arrows
- no learned confidence calibration
- no explicit dataset/evaluation framework

Do not replace it automatically with deep learning. First measure where it fails.

### 3.2 Solver

`solver/graph.py` is named `GraphSolver`, but the current implementation does not build a persistent graph.

It:

- receives the current binary mask and detected arrows
- scans a narrow screen-space band from each arrow in its direction
- decides whether another visible obstacle exists in that ray
- returns arrows considered immediately shootable

This is a **local visibility/ray heuristic**, not a complete puzzle graph or global planner.

This distinction must remain explicit in all future work.

### 3.3 Executor

`executor/bot.py` currently:

1. captures a screenshot
2. checks the lives/status ROI
3. creates a binary board mask
4. detects arrows
5. calls the local solver
6. taps only the first returned arrow
7. sleeps
8. captures a new screenshot
9. repeats

This means the system currently has no persistent memory of previously observed arrows.

The loop is therefore fundamentally reactive and viewport-local.

---

## 4. Actual Problem

The initial problem formulation was approximately:

> Detect arrows on the screen and click an arrow whose path is clear.

This formulation is insufficient for Hard and Super Hard levels.

Manual play has demonstrated that larger levels may require:

- scrolling the viewport
- inspecting regions that are not currently visible
- remembering what was observed before scrolling
- reasoning about relationships between objects across different screen positions

Therefore the real problem is better described as:

> **Partially observable puzzle solving with visual perception, multi-viewport state reconstruction, planning, UI control, and verification.**

The project should treat the following as separate failure modes:

### PERCEPTION

An arrow is visible but is not detected or classified correctly.

### LOCALIZATION

An arrow is detected but its position cannot be related reliably to other observations.

### WORLD_MODEL

Multiple observations are individually correct but cannot be merged into one consistent puzzle representation.

### EXPLORATION

The system does not know when/how to scroll and inspect unseen regions.

### SOLVER

The complete relevant state is available, but the chosen move is wrong.

### CONTROL

The selected action is correct, but the ADB interaction fails or targets the wrong location.

### VERIFICATION

The action happens, but the system incorrectly interprets the new state.

When debugging, identify the failure category before changing the architecture.

---

## 5. Core Architectural Target

The desired architecture is:

```text
Capture
   ↓
Perception
   ↓
Observation
   ↓
World Model  ←── viewport/scroll alignment
   ↓
Exploration / Information Check
   ↓
Solver / Planner
   ↓
Controller
   ↓
Verification
   ↓
Updated World Model
   ↺
```

The critical new concept is a persistent **World Model**.

Screen coordinates must not be treated as permanent object coordinates.

Conceptually:

```text
screen coordinates
        ↓
viewport transform
        ↓
world/logical coordinates
```

The same logical arrow observed before and after scrolling must be capable of being represented as the same object.

Unexplored areas must be represented as **unknown**, not silently as empty.

---

## 6. Observation Model

Future perception code should preferably produce structured observations rather than directly controlling the game.

A conceptual observation may contain:

```text
Observation
├── timestamp
├── viewport information
├── detected objects
│   ├── position
│   ├── direction
│   ├── size
│   ├── visibility
│   └── confidence
└── capture metadata
```

The exact Python types are an implementation decision and must be based on the existing codebase when implemented.

---

## 7. World Model Requirements

The world model should eventually support:

- persistent object identity
- multiple observations of the same object
- viewport transformations
- duplicate merging
- partially visible objects
- confidence/uncertainty
- explored vs unexplored regions
- state changes after actions
- removal or mutation of solved arrows
- consistency checks

The first implementation does not need to be perfect.

A small, testable world model is preferable to a large speculative framework.

---

## 8. Exploration Requirements

The system must be able to answer:

> Do I know enough to make this move safely?

If yes:

```text
plan → act
```

If no:

```text
explore → observe → update world model → re-evaluate
```

The system must not make irreversible moves based solely on the assumption that unseen regions are irrelevant.

Two broad strategies should be evaluated:

### Full exploration

Explore the relevant board before solving.

### Incremental exploration

Explore only when the current information is insufficient.

A hybrid approach may ultimately be best.

This is an experiment, not a predetermined architectural fact.

---

## 9. Deep Learning Policy

Deep learning is a candidate solution for **perception**, not a default solution for the whole problem.

Do not train a model until the current detector has been evaluated on a representative dataset.

Before training, establish:

- what the model should predict
- annotation format
- dataset size
- train/validation/test split
- baseline detector performance
- evaluation metrics
- expected improvement
- inference constraints

A model that detects arrows perfectly will still not solve:

- scrolling
- world reconstruction
- exploration
- planning
- action verification

unless those components are separately designed.

---

## 10. Development Principles

### Evidence over intuition

Measure the failure before choosing the solution.

### Separation of concerns

Perception, world modeling, solver logic, controller, and verification should remain testable independently.

### Minimal change

Prefer the smallest implementation that tests a hypothesis.

### Reproducibility

Save representative screenshots, recordings, or fixtures for important failures.

### No fabricated evidence

Never claim that tests, benchmarks, screenshots, or commands were checked unless they actually were.

### Unknown is not empty

An unobserved region is unknown.

### Verify state transitions

Do not assume a tap succeeded merely because ADB accepted the command.

---

## 11. Success Criteria

The final system should be evaluated at both component and puzzle levels.

### Perception

- detection precision/recall
- false positives
- false negatives
- direction classification accuracy

### World Model

- duplicate-object rate
- cross-viewport identity accuracy
- coordinate alignment error
- reconstruction completeness

### Solver

- valid-move accuracy
- invalid-move rate
- solved-puzzle rate on known states

### Automation

- puzzle completion rate
- average solve time
- unnecessary scroll count
- recovery rate
- unexpected-action rate

The most important end-to-end metric is:

> **Reliable puzzle completion across representative Easy, Hard, and Super Hard scenarios.**

---

## 12. Definition of Done

A feature is not complete because code exists.

A meaningful change is complete when:

1. The relevant implementation was inspected.
2. The failure/problem was clearly identified.
3. The change was implemented.
4. Appropriate tests or evaluation were run.
5. Results were recorded honestly.
6. Remaining limitations are documented.
7. Major architectural decisions are recorded when necessary.

---

## 13. Documentation Sources of Truth

```text
PROJECT.md
    Project definition and current architectural reality

AGENTS.md
    Instructions for AI coding agents

CLAUDE.md
    Claude Code entry point and Claude-specific instructions

docs/roadmap.md
    Development plan and current priorities

docs/experiments/
    Experimental hypotheses and measured results

docs/decisions/
    Accepted/rejected architectural decisions
```

When documentation conflicts with source code, inspect the source code and resolve the discrepancy explicitly rather than silently assuming either side is correct.
