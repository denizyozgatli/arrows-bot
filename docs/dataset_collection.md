# Dataset Collection Guide

This guide explains how to collect a high-quality, diverse dataset for the future
learned arrow detector / false-positive rejection model.

## Core concepts

### Difficulty and viewport count are INDEPENDENT

Never assume:

- Easy = single viewport
- Hard = multi-viewport
- Super Hard = multi-viewport

All of these are valid:

- Easy + 1 viewport
- Easy + multiple viewports
- Hard + 1 viewport
- Hard + multiple viewports
- Super Hard + 1 viewport
- Super Hard + multiple viewports

A Hard or Super Hard level may fit entirely in one screenshot. An Easy level may
require scrolling. Record both properties truthfully; do not infer one from the other.

### A "level" is not a "viewport"

One level may produce several screenshots (the same board state observed from
different scroll positions), or exactly one. All screenshots of the same level
share one `level_id`.

## Directory structure

New collections use a level-based structure:

```
data/raw/<level_id>/
    viewport_001.png
    viewport_002.png
    metadata.json

data/annotations/<level_id>/
    viewport_001.json
    viewport_002.json
```

The existing flat `data/raw/easy/` and `data/raw/hard/` data is left untouched and
still works with the evaluator.

## Metadata format

`data/raw/<level_id>/metadata.json`:

```json
{
  "level_id": "level_001",
  "difficulty": "hard",
  "viewport_count": 3,
  "collection_session": "2026-08-31",
  "notes": "dense board, many maze corners",
  "screen_width": 1080,
  "screen_height": 2400,
  "viewports": [
    {"viewport_index": 1, "file": "viewport_001.png"},
    {"viewport_index": 2, "file": "viewport_002.png"},
    {"viewport_index": 3, "file": "viewport_003.png"}
  ]
}
```

- `level_id`: unique identifier for the level (e.g. `level_001`).
- `difficulty`: one of `easy`, `hard`, `super_hard`.
- `viewport_count`: total number of screenshots collected for this level.
- `viewport_index`: position of a viewport within the level's sequence.
- Optional: `collection_session`, `notes`, `screen_width`, `screen_height`.

## Collection tooling

Two commands are available (run from the repo root with `PYTHONPATH=src`):

```
python -m arrows_bot.eval.cli collect-level --level-id level_001 --difficulty hard --count 1
python -m arrows_bot.eval.cli validate-level --level-id level_001
```

`collect-level` only captures screenshots, names them, and writes metadata. It
never scrolls, taps, chooses arrows, or plays the game. The human controls all
gameplay and viewport changes.

## How to collect a single-viewport level

1. Open the level in the game so the full board is visible in one view.
2. Run:
   ```
   python -m arrows_bot.eval.cli collect-level --level-id level_001 --difficulty easy --count 1
   ```
3. This saves `data/raw/level_001/viewport_001.png` and writes `metadata.json`
   with `viewport_count: 1`.
4. Validate: `python -m arrows_bot.eval.cli validate-level --level-id level_001`.

## How to collect a multi-viewport level

1. Open the level in its initial view.
2. Run:
   ```
   python -m arrows_bot.eval.cli collect-level --level-id level_002 --difficulty hard --count 1
   ```
   This captures `viewport_001.png`.
3. Manually change the viewport (scroll/pan) to the next region.
4. Run the same command again (same `level_id`). It appends `viewport_002.png`.
5. Repeat until the relevant board area has been observed.
6. `metadata.json` records the total `viewport_count` and each `viewport_index`.

Notes:
- Do not scroll automatically; the human changes the viewport.
- Do not assume a fixed scroll direction or a fixed overlap between views.
- Do not assume every viewport has the same number of arrows.

## Ground-truth annotation

Ground truth is created manually by the human. Use the existing annotator:

```
python -m arrows_bot.eval.cli annotate --image data/raw/level_001/viewport_001.png --terminal
```

Annotation format (unchanged):

```json
{
  "image": "viewport_001.png",
  "arrows": [
    {"x": 123, "y": 456, "direction": "UP"}
  ]
}
```

Never generate ground truth from detector output. Detector predictions are not
annotation truth.

### Partially visible arrows

- If the arrow's center/tap point is visible and its direction can be determined
  reliably, annotate it.
- If the arrow is too partially visible to determine its center/direction
  reliably, do NOT guess. Record it as "unusable for annotation" in the level's
  `notes` instead.

## Recommended 10–20 level collection strategy

Target roughly:

- 4–6 Easy levels
- 4–7 Hard levels
- 4–7 Super Hard levels

Do NOT enforce viewport count by difficulty. Deliberately seek a mixture:

- single-viewport Easy
- multi-viewport Easy
- single-viewport Hard
- multi-viewport Hard
- single-viewport Super Hard
- multi-viewport Super Hard

Prioritize diversity and truthful metadata over exact quotas. If the game does
not naturally provide a combination, do not force it.

### Visual diversity to seek

- sparse boards (5–15 arrows)
- medium-density boards (15–40 arrows)
- dense boards (40+ arrows)
- many maze corners
- long maze corridors
- arrows near maze geometry
- arrows near viewport edges
- partially visible arrows
- different arrow orientations
- different arrow scales (if present)
- different board layouts / visual arrangements

### Avoiding duplicate levels

- Use a unique `level_id` for each new level.
- If you re-run `collect-level` with an existing `level_id` and a different
  difficulty, the tool warns you — this usually means you are reusing an id.

## What to bring back after collection

For each level, return:

- the `data/raw/<level_id>/` directory (screenshots + `metadata.json`)
- the `data/annotations/<level_id>/` directory (one JSON per viewport)
- truthful `difficulty` and `viewport_count` in metadata
- notes on any partially visible / unusable arrows

## ML dataset note

The future classifier/detector needs both positive and negative examples:

- Positive: real arrows.
- Negative: maze wall segments, corners, corridor geometry, arrow-like wall
  structures, and other structures the template matcher mistakes for arrows.

The existing benchmark already provides ~320 positive arrows and ~224
false-positive candidates. The collection tooling is designed so that detector
false positives can later be captured as candidate patches (positive/negative
crops) from the same screenshots.
