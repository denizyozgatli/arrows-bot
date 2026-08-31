# Arrow Solver — Project Context

## 1. PROJECT GOAL

Arrow Solver is a Python Android-game automation project.

The target game is an arrow/maze puzzle.

The long-term goal is:

1. Observe the game board.
2. Detect real arrows reliably.
3. Distinguish arrows from maze/wall geometry.
4. Build a global representation of the board.
5. Handle boards that require multiple viewport screenshots.
6. Determine safe arrow-removal order.
7. Execute taps through ADB.
8. Verify state changes and recover safely.

The project is NOT currently production-ready.

The current system is an experimental prototype.

---

## 2. CRITICAL GAME OBSERVATION

Difficulty and viewport count are INDEPENDENT.

DO NOT assume:

Easy = single viewport
Hard = multi viewport
Super Hard = multi viewport

Valid combinations include:

Easy + single viewport
Easy + multiple viewports
Hard + single viewport
Hard + multiple viewports
Super Hard + single viewport
Super Hard + multiple viewports

This distinction MUST be preserved in all future dataset design and architecture.

The bot should ultimately determine whether the COMPLETE board is visible rather than deciding whether to scroll based on difficulty.

---

## 3. CURRENT ARCHITECTURE

Important source files:

src/arrows_bot/
    adb/
    vision/
        detector.py
        mapper.py
    solver/
        graph.py
        navigator.py
    executor/
        bot.py
    eval/
        collect.py
        annotate.py
        evaluate.py
        report.py
        cli.py

Current reality:

- detector.py contains the current template-matching detector.
- mapper.py is currently not implemented as a complete global board mapper.
- navigator.py is currently not implemented as a complete viewport navigation system.
- graph.py uses the current heuristic/ray-based solving approach.
- bot.py contains the current execution loop.
- eval/ contains the offline dataset/evaluation tooling.

Do NOT assume documentation describes implemented functionality.
Source code is authoritative.

---

## 4. CURRENT DETECTOR BASELINE

The current detector is template-matching based.

Benchmark dataset:

shot_0001
shot_0004
shot_0005
shot_0006
shot_0007
shot_0008
shot_0009

Total ground-truth arrows:

320

Baseline threshold 0.72:

GT = 320
detections = 644
TP = 320
FP = 324
FN = 0

Precision = 0.497
Recall = 1.000
F1 = 0.664
Direction accuracy = 0.978
Average position error = 10.25 px

---

## 5. THRESHOLD SWEEP

Measured thresholds:

0.72:
precision 0.497
recall 1.000
F1 0.664

0.74:
precision 0.510
recall 1.000
F1 0.675

0.76:
precision 0.588
recall 1.000
F1 0.741

0.78:
precision 0.858
recall 0.944
F1 0.899

0.80:
precision 0.933
recall 0.347
F1 0.506

0.82:
precision 1.000
recall 0.075
F1 0.140

0.84+:
no detections

Current safe baseline threshold:

0.76

because it preserves 100% recall while improving precision.

However, precision remains only 58.8%.

Do NOT claim 0.78 is safe because it causes 18 false negatives.

---

## 6. FALSE POSITIVE ANALYSIS

At threshold 0.76:

TP = 320
FP = 224
FN = 0

All 224 FPs are associated with maze geometry.

FP categories:

Maze/wall line segment:
82 / 224 = 36.6%

Maze wall corner/junction:
103 / 224 = 46.0%

Wall segment adjacent to real arrow:
39 / 224 = 17.4%

Duplicates:
0

UI/background:
0

Border artifacts:
0

Wrong-direction FP:
0

Therefore approximately 100% of false positives are maze/wall geometry.

---

## 7. TP VS FP SCORE DISTRIBUTION

TP:

min 0.7762
max 0.8278
mean 0.7981
median 0.7967
p90 0.8126
p95 0.8228

FP:

min 0.7612
max 0.8032
mean 0.7733
median 0.7700
p90 0.7829
p95 0.7968

There is significant score overlap.

Therefore threshold-only filtering cannot solve the problem.

---

## 8. ROOT CAUSE

Dominant causes:

1. Maze/wall geometry
2. Template shape ambiguity
3. Insufficient geometric constraints
4. Score overlap

Not significant:

- duplicate detection
- border artifacts
- direction ambiguity

The template matcher detects real arrows very well but also detects wall/corridor geometry.

---

## 9. CURRENT ML STRATEGY

Do NOT immediately replace the detector with YOLO.

The preferred next experiment is:

Template matching
    ↓
candidate detections
    ↓
small learned false-positive rejection model
    ↓
real arrow

The learned model only needs to answer:

"Is this candidate a real arrow or maze geometry?"

This is a substantially smaller problem than full object detection.

Potential classifier:

- small CNN
- candidate image crop
- output probability: arrow / not-arrow

Potential additional features:

- template score
- local geometry
- brightness
- fill
- aspect ratio
- color

Do not train yet until sufficient independent data exists.

---

## 10. CURRENT DATASET

Existing ground-truth annotations:

shot_0001 = 43 arrows
shot_0004 = 46 arrows
shot_0005 = 44 arrows
shot_0006 = 54 arrows
shot_0007 = 35 arrows
shot_0008 = 40 arrows
shot_0009 = 58 arrows

Total = 320 arrows.

shot_0005 is explicitly HARD and has viewport_count = 1.

Do NOT infer viewport count from difficulty.

---

## 11. DATA COLLECTION SYSTEM

The dataset collection tooling has been implemented.

New CLI commands:

collect-level
validate-level

Example:

python -m arrows_bot.eval.cli collect-level --level-id level_001 --difficulty easy --count 1

Multi-viewport example:

python -m arrows_bot.eval.cli collect-level --level-id level_002 --difficulty hard --count 1

Human manually changes viewport.

Then:

python -m arrows_bot.eval.cli collect-level --level-id level_002 --difficulty hard --count 1

Repeat for additional viewports.

No automatic scrolling is allowed during dataset collection.

---

## 12. DATASET METADATA

Preferred metadata:

{
  "level_id": "level_001",
  "difficulty": "hard",
  "viewport_count": 3,
  "collection_session": "YYYY-MM-DD",
  "notes": "...",
  "screen_width": 1080,
  "screen_height": 2400,
  "viewports": [
    {
      "viewport_index": 1,
      "file": "viewport_001.png"
    }
  ]
}

difficulty values:

easy
hard
super_hard

viewport_count is independent of difficulty.

---

## 13. NEW DATA COLLECTION TARGET

Target approximately 10–20 additional levels.

Suggested rough distribution:

4–6 Easy
4–7 Hard
4–7 Super Hard

But these are NOT strict quotas.

More important:

- single viewport examples
- multi viewport examples
- dense boards
- sparse boards
- maze-heavy boards
- arrows near maze geometry
- arrows near edges
- partial visibility
- different arrow arrangements
- different scales if naturally present

Easy + multi-viewport is valid.

Hard + single-viewport is valid.

Super Hard + single-viewport is valid.

---

## 14. LEVEL VS VIEWPORT

A level is one logical board.

Example:

level_001/
    viewport_001.png
    viewport_002.png
    viewport_003.png
    metadata.json

These are THREE views of ONE level.

They are NOT three independent levels.

This distinction is critical for future ML train/validation/test splitting.

All viewports from the same level MUST remain in the same dataset split.

Never put viewport_001 into train and viewport_002 from the same level into test.

---

## 15. GROUND TRUTH

Ground truth is manually created.

Existing annotation format:

{
  "image": "viewport_001.png",
  "arrows": [
    {
      "x": 123,
      "y": 456,
      "direction": "UP"
    }
  ]
}

Never generate ground truth from detector predictions.

Partially visible arrows:

- annotate if center and direction are reliably determinable
- otherwise do not guess

---

## 16. LATEST DATA COLLECTION

Latest collected level:

level_2298

Difficulty:
easy

Viewport count:
1

Screenshot:

data/raw/level_2298/viewport_001.png

Metadata:

data/raw/level_2298/metadata.json

The screenshot has been manually inspected and ground-truth arrows were identified.

The current annotation list for this image is:

174 660 RIGHT
311 660 RIGHT
720 660 RIGHT
381 662 UP
586 662 UP
347 662 UP
690 729 LEFT
520 763 LEFT
42 763 LEFT
827 763 LEFT
176 764 UP
756 764 UP
722 764 UP
312 764 UP
618 797 RIGHT
246 797 LEFT
381 798 UP
755 831 RIGHT
449 832 UP
108 832 UP
552 833 UP
244 833 UP
315 865 LEFT
827 865 LEFT
859 935 UP
246 968 LEFT
789 968 RIGHT
415 969 UP
40 999 DOWN
550 1070 RIGHT
278 1102 DOWN
315 1104 LEFT
790 1106 UP
212 1138 LEFT
74 1204 DOWN
859 1238 DOWN
281 1241 LEFT
793 1241 LEFT
178 1241 LEFT
383 1241 LEFT
823 1275 RIGHT
39 1307 DOWN
210 1307 DOWN
110 1309 LEFT
654 1375 DOWN
756 1409 DOWN
859 1409 DOWN
108 1413 UP
516 1445 RIGHT
417 1446 LEFT
756 1477 DOWN
790 1481 UP
313 1511 DOWN
552 1511 DOWN
209 1513 RIGHT
721 1513 RIGHT
277 1514 RIGHT
42 1514 LEFT

Total:
58 arrows

These coordinates are human ground truth.
Do not replace them with detector output.

---

## 17. CURRENT DEVELOPMENT PRIORITY

Priority order:

1. Build a reliable ML false-positive rejection experiment.
2. Validate it on unseen LEVELS.
3. Improve perception precision.
4. Then design global board mapping.
5. Then design viewport exploration / scrolling.
6. Then build global dependency representation.
7. Then redesign planner/solver.
8. Finally integrate safe gameplay execution.

Do not jump directly to reinforcement learning.

Do not assume YOLO is required.

---

## 18. FUTURE MULTI-VIEW ARCHITECTURE

The final bot should NOT decide to scroll because of difficulty.

Instead:

observe current viewport
    ↓
detect arrows
    ↓
determine whether board state is complete/partially observed
    ↓
if incomplete:
    explore another viewport
    ↓
align observations into global board coordinates
    ↓
build global board state
    ↓
solve
    ↓
execute
    ↓
observe again
    ↓
update world model

The system should be able to handle:

Easy + 1 viewport
Easy + multiple viewports
Hard + 1 viewport
Hard + multiple viewports
Super Hard + 1 viewport
Super Hard + multiple viewports

---

## 19. IMPORTANT DEVELOPMENT RULE

Do not make large architectural changes without an offline benchmark.

Every perception change must be evaluated against a held-out dataset.

Every planning change should be tested offline when possible.

Do not use real gameplay as the primary debugging loop because lives are limited.

The offline evaluation system is a core part of the project.

---

## 20. IMMEDIATE NEXT STEP

The immediate next step is:

Collect approximately 10–20 additional diverse levels.

Then:

1. manually annotate them
2. generate candidate positives/negatives from the existing template matcher
3. split by LEVEL, not screenshot
4. train a small false-positive classifier
5. evaluate on unseen levels
6. compare against the 0.76 template baseline

Do not implement the classifier before the independent dataset is ready.