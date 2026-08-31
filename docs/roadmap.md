# Arrow Solver — Development Roadmap

## Status

**Current phase: Phase 0 — Baseline and failure isolation**

The existing implementation is a prototype that can perform local, screen-space detection and action selection, but it is not yet architecturally capable of reliably solving large multi-viewport levels.

The roadmap deliberately does **not** begin with "train a neural network".

The first objective is to determine which failure modes actually prevent reliable solving.

---

# Phase 0 — Freeze and Measure the Current Baseline

## Goal

Create a reproducible baseline for the failed implementation.

## Tasks

- [ ] Preserve the current implementation as a known baseline.
- [ ] Capture representative Easy scenarios.
- [ ] Capture representative Hard scenarios.
- [ ] Capture representative Super Hard scenarios.
- [ ] Include levels where the complete puzzle fits in one viewport.
- [ ] Include levels that require scrolling.
- [ ] Include partially visible arrows.
- [ ] Save screenshots before and after important actions.
- [ ] Record failed runs.
- [ ] Classify each failure.

## Failure Labels

```text
PERCEPTION
LOCALIZATION
WORLD_MODEL
EXPLORATION
SOLVER
CONTROL
VERIFICATION
UNKNOWN
```

## Important

Do not modify the baseline solely to make a particular run look better.

The baseline is useful only if failures remain reproducible.

## Exit Criteria

Have a small but representative evaluation set and a written failure report.

---

# Phase 1 — Audit the Existing Perception System

## Goal

Determine whether template matching is actually the dominant bottleneck.

Current baseline:

```text
bright-pixel threshold
        ↓
synthetic arrow templates
        ↓
multi-scale cv2.matchTemplate
        ↓
proximity duplicate suppression
```

## Tasks

- [ ] Run the detector offline on saved screenshots.
- [ ] Manually establish expected arrow locations/classes.
- [ ] Measure missed detections.
- [ ] Measure false positives.
- [ ] Measure direction errors.
- [ ] Test different arrow sizes.
- [ ] Test partially visible arrows.
- [ ] Test Hard/Super Hard screenshots.
- [ ] Record representative detector failures.

## Decision Gate

### If detection is poor

Proceed to Phase 2A and evaluate improved perception methods.

### If detection is acceptable

Do not replace the detector yet.

Proceed to multi-viewport/world-model work.

---

# Phase 2A — Improve Perception Only If Evidence Requires It

## Goal

Find the simplest perception method that meets the required accuracy.

Evaluate in increasing complexity.

### Candidate A — Better Classical CV

Consider:

- contour analysis
- connected components
- morphology
- geometric filtering
- improved direction estimation
- adaptive thresholds
- better duplicate suppression

### Candidate B — Learned Object Detection

Consider a detector such as a YOLO-family or RT-DETR-family model only after a dataset exists.

### Candidate C — Custom Model

Only consider custom architecture if existing models are unsuitable for the specific visual problem.

## Required Before Training

- [ ] Define label schema.
- [ ] Build dataset.
- [ ] Separate train/validation/test sets.
- [ ] Avoid near-duplicate leakage.
- [ ] Define baseline.
- [ ] Define metrics.
- [ ] Define acceptance threshold.

## Exit Criteria

Perception is good enough that remaining failures can be meaningfully investigated at the world-model/solver level.

---

# Phase 2 — Build a Persistent Observation Model

## Goal

Separate what the camera sees from what the agent believes exists in the puzzle.

Introduce a structured observation concept.

Conceptually:

```text
Screenshot
    ↓
Perception
    ↓
Observation
```

An observation should eventually include:

- detected objects
- screen positions
- directions
- sizes
- visibility
- confidence
- viewport metadata

Do not couple this directly to ADB actions.

## Exit Criteria

The detector can be tested independently and produces structured observations.

---

# Phase 3 — Build the World Model

## Goal

Solve the fundamental multi-viewport problem.

Current state:

```text
screenshot A → solve locally → tap
screenshot B → solve locally → tap
screenshot C → solve locally → tap
```

Target:

```text
screenshot A ─┐
screenshot B ─┼→ persistent world model
screenshot C ─┘
```

## Core Requirements

- [ ] Represent persistent objects.
- [ ] Track object identity.
- [ ] Distinguish screen and world coordinates.
- [ ] Store viewport transforms.
- [ ] Merge overlapping observations.
- [ ] Avoid duplicate objects.
- [ ] Represent partially observed objects.
- [ ] Represent unexplored regions.
- [ ] Update state after actions.

## Coordinate Model

At minimum distinguish:

```text
screen position
viewport position
world/logical position
```

The exact transformation method is an experiment.

---

# Phase 4 — Determine Viewport Alignment Strategy

## Goal

Determine how observations from different scroll positions should be aligned.

Evaluate:

### Option A — Scroll-offset tracking

Track the intended scroll movement and transform coordinates.

### Option B — Visual registration

Use overlapping image information to estimate displacement.

Possible techniques:

- feature matching
- image registration
- template/landmark matching

### Option C — Hybrid

Use known scroll movement as an initial estimate and visual information as correction.

## Important

Do not choose a method because it sounds sophisticated.

Use representative recordings to measure alignment error and robustness.

## Exit Criteria

The system can observe the same region at multiple scroll positions without creating inconsistent duplicate world objects.

---

# Phase 5 — Build Exploration

## Goal

Allow the agent to discover information outside the current viewport.

The agent needs an explicit concept of:

```text
known
unknown
```

## Strategy 1 — Full Exploration

```text
scan
→ scroll
→ scan
→ scroll
→ reconstruct
→ solve
```

## Strategy 2 — Incremental Exploration

```text
observe
→ is the next action safe with current knowledge?
    ├── yes → act
    └── no  → explore
```

## Strategy 3 — Hybrid

Perform enough initial exploration to build a useful map, then explore only when required.

## Tasks

- [ ] Detect whether more board remains outside the viewport.
- [ ] Define scroll actions.
- [ ] Record viewport transitions.
- [ ] Avoid endless scrolling loops.
- [ ] Detect repeated/unchanged views.
- [ ] Mark explored regions.
- [ ] Reconstruct state after each exploration step.

## Exit Criteria

The agent can systematically inspect a multi-viewport level and return to a consistent world model.

---

# Phase 6 — Extract and Validate the Actual Puzzle Solver

## Goal

Separate puzzle reasoning from image processing.

The solver should eventually consume structured state:

```text
WorldState
    ↓
Solver
    ↓
Action
```

rather than raw screenshots.

## Tasks

- [ ] Define a minimal puzzle-state representation.
- [ ] Create synthetic/manually defined states.
- [ ] Test legal moves.
- [ ] Test blocked moves.
- [ ] Test dependency relationships.
- [ ] Test incomplete states.
- [ ] Test ambiguous states.
- [ ] Compare solver output with known solutions.

## Exit Criteria

The solver can be tested without running the real game.

This is critical for distinguishing perception/world-model bugs from reasoning bugs.

---

# Phase 7 — Closed-Loop Controller

## Goal

Replace the current open-loop assumption with verified state transitions.

Target:

```text
Observe
  ↓
Update world state
  ↓
Plan
  ↓
Execute
  ↓
Observe again
  ↓
Verify
  ↓
Update state
```

## Tasks

- [ ] Add explicit action objects.
- [ ] Add before/after observations.
- [ ] Detect whether an arrow disappeared/changed.
- [ ] Detect unexpected screen changes.
- [ ] Detect failed taps.
- [ ] Handle animation delays.
- [ ] Stop safely when verification fails.

## Exit Criteria

The system does not blindly assume that an ADB tap produced the intended game-state change.

---

# Phase 8 — End-to-End Evaluation Harness

## Goal

Create a repeatable benchmark for every future architectural change.

## Scenario Groups

### Easy

- single viewport
- low visual complexity

### Hard

- larger puzzle
- multiple relevant regions
- scrolling

### Super Hard

- large puzzle
- multiple viewport transitions
- partial observations

### Edge Cases

- partial arrows
- visually ambiguous arrows
- repeated patterns
- unexpected UI states
- failed actions
- repeated viewport images

## Metrics

Track at least:

```text
arrow detection precision
arrow detection recall
direction accuracy
world-model duplicate rate
world-coordinate alignment error
correct-move rate
invalid-move rate
scroll count
unnecessary scroll count
puzzle completion rate
solve time
verification failure rate
```

---

# Phase 9 — Optimize

Only optimize after correctness is established.

Possible optimizations:

- fewer screenshots
- fewer scrolls
- cached observations
- faster perception
- batching
- reduced duplicate processing
- improved exploration policy

Do not optimize a system whose correctness has not been established.

---

# Phase 10 — Production Hardening

## Tasks

- [ ] Robust ADB error handling.
- [ ] Connection retry strategy.
- [ ] Timeouts.
- [ ] Structured logging.
- [ ] Run/session IDs.
- [ ] Screenshot/event artifacts for failures.
- [ ] Safe stop behavior.
- [ ] Configuration validation.
- [ ] Clean removal of generated `__pycache__` artifacts from source control if applicable.
- [ ] Automated tests in CI where practical.
- [ ] Reproducible environment setup.

---

# Immediate Next Steps

Do these in order.

## Step 1

Create a baseline dataset from the current failed implementation.

## Step 2

Run the existing detector offline against that dataset.

## Step 3

Classify failures.

## Step 4

Measure how often failures are perception failures versus failures caused by the single-viewport architecture.

## Step 5

Implement the smallest persistent observation/world-state prototype.

## Step 6

Build a controlled multi-viewport experiment before integrating it into the live bot.

## Step 7

Only after the above evidence, decide whether a learned detector is necessary.

---

# Explicitly Deferred Decisions

The following are intentionally **not decided yet**:

- YOLO vs RT-DETR vs custom model
- classical CV vs deep learning
- exact world-coordinate representation
- exact scroll-alignment algorithm
- full exploration vs incremental exploration
- exact graph representation
- exact solver algorithm

These should be decided from experiments rather than assumptions.

---

# What Success Looks Like

The final system should not behave like:

```text
screenshot
→ detect visible arrows
→ click one
→ forget previous screen
→ screenshot
→ repeat
```

It should behave like:

```text
observe
→ perceive
→ remember
→ identify unknown information
→ explore when necessary
→ reconstruct state
→ plan
→ act
→ verify
→ update state
→ repeat
```

The fundamental project objective is therefore:

> **Build a reliable agent that maintains enough persistent knowledge of the puzzle to solve it across multiple viewport positions, rather than merely detecting and clicking arrows visible in the current screenshot.**
