# Arrow Solver — Agent Instructions

## 1. Read First

Before making a non-trivial change, read:

- `PROJECT.md`
- `docs/roadmap.md` if the task affects architecture or direction
- the relevant source files
- existing tests/evaluation fixtures if present

Do not assume that architecture described in documentation is already implemented.

---

## 2. Repository Source of Truth

The current implementation is a prototype.

In particular:

- `vision/detector.py` uses handcrafted template matching.
- `vision/mapper.py` is currently empty.
- `solver/navigator.py` is currently empty.
- `solver/graph.py` is a screen-space ray heuristic, not a persistent graph.
- `executor/bot.py` repeatedly captures the current viewport and acts on one locally selected arrow.
- There is currently no persistent multi-viewport world model.

Do not describe planned components as implemented components.

---

## 3. Required Workflow

For non-trivial tasks:

```text
Inspect
→ Understand
→ Identify failure
→ Form hypothesis
→ Plan
→ Implement
→ Verify
→ Document
```

Do not immediately rewrite the system when a test fails.

---

## 4. Failure Classification

Before changing an algorithm, classify the failure when possible:

- `PERCEPTION`
- `LOCALIZATION`
- `WORLD_MODEL`
- `EXPLORATION`
- `SOLVER`
- `CONTROL`
- `VERIFICATION`
- `UNKNOWN`

If the failure is `UNKNOWN`, gather evidence before committing to a major solution.

---

## 5. Multi-Viewport Rule

Never assume the current screenshot contains the complete puzzle.

Hard and Super Hard levels may require scrolling.

Unseen regions are:

```text
UNKNOWN
```

not:

```text
EMPTY
```

Do not make an irreversible action based on an unsupported assumption about an unseen region.

---

## 6. Separation of Responsibilities

Prefer this data flow:

```text
Capture
→ Perception
→ Observation
→ World Model
→ Exploration / Planning
→ Controller
→ Verification
```

Do not put global puzzle logic into the screenshot capture layer.

Do not make low-level ADB code responsible for puzzle decisions.

Do not make the detector depend directly on mouse/ADB control.

---

## 7. Inspect Before Editing

Before modifying a file:

1. Read the current implementation.
2. Search for callers and dependencies.
3. Check whether an equivalent mechanism already exists.
4. Identify assumptions made by surrounding code.
5. Prefer a small compatible change.

Do not invent APIs, modules, paths, commands, or configuration values.

---

## 8. Deep Learning

Do not introduce deep learning simply because the current approach fails.

First establish whether the bottleneck is perception.

If ML is justified, define:

- input
- target output
- labels
- dataset
- train/validation/test split
- baseline
- metrics
- acceptance threshold

A detector model cannot by itself solve multi-viewport state reconstruction or planning.

---

## 9. Testing and Verification

Never claim a test passed unless it was actually run.

After changes, report:

### Changed

What changed?

### Why

What problem does it address?

### Verified

What tests/evaluations actually ran?

### Remaining Risks

What remains uncertain?

If a real-device test cannot be performed, say so.

---

## 10. Experiments

For significant algorithmic experiments, use:

```text
docs/experiments/
```

Recommended format:

```md
# Experiment — <name>

## Problem

## Hypothesis

## Approach

## Dataset / Scenarios

## Metrics

## Results

## Conclusion

## Decision
```

Use measured results to decide whether an approach should continue.

---

## 11. Architectural Decisions

For significant architecture changes, create an ADR under:

```text
docs/decisions/
```

Include:

- Context
- Problem
- Decision
- Alternatives
- Evidence
- Consequences

Do not repeatedly revive rejected approaches without new evidence.

---

## 12. Minimal Change Principle

Do not:

- refactor unrelated code
- rewrite working modules without evidence
- add speculative abstractions
- add dependencies without justification
- implement future features that are not required by the current task

If a rewrite is necessary, explain why incremental modification is insufficient.

---

## 13. Data and Coordinates

Treat these as distinct concepts:

```text
screen coordinates
viewport coordinates
world/logical coordinates
```

Do not use raw screen coordinates as persistent object identity.

When scrolling is introduced, explicitly define how observations are aligned.

---

## 14. State and Actions

Prefer:

```text
Observe
→ Update state
→ Determine whether information is sufficient
→ Plan
→ Act
→ Verify
→ Update state
```

over:

```text
Screenshot
→ Guess
→ Click
```

Every important action should eventually have a verification path.

---

## 15. Documentation Maintenance

When implementation changes the architecture:

- update `PROJECT.md` if the durable project reality changed
- update `docs/roadmap.md` if priorities/status changed
- add an experiment record for significant experiments
- add an ADR for significant architectural decisions

Do not let documentation describe nonexistent functionality.

---

## 16. Honesty Rule

Never fabricate:

- test results
- benchmark values
- model accuracy
- screenshots inspected
- files inspected
- command output
- successful puzzle runs

If something is unknown, say it is unknown and explain what evidence would resolve it.

---

## 17. Core Principle

The goal is not to maximize code output.

The goal is to maximize the probability of correctly solving the puzzle.

Prefer:

```text
measured understanding
over
speculative implementation
```
