# Emberbrook: Skyshard Valley

A fully playable 2D cozy farming RPG inspired by the farming-life genre, with an original world, cast, story arc, map layout, progression, and visual style.

## What is implemented

- **Player controls (WASD)** for real-time movement in a tile world.
- **Sprite-based visuals** with animated player walk cycle, animated water tiles, NPC sprites, and crop growth visuals.
- **Crop farming loop**: planting, watering, growth progression by day, harvesting, seasonal withering.
- **Mining + fishing loops** tied to world zones and stamina costs.
- **Crafting + survival** via Trail Ration recipe and stamina recovery.
- **Relationships** with unique NPCs (Iri, Tomas, Sel), gift preferences, bond growth.
- **Progression events**:
  - Day-gated mine unlock.
  - Lantern Bloom Festival payout.
  - Sky Shrine restoration from village bonds (max stamina upgrade).
- **Day-night cycle and season/year progression**.

## Install and run

```bash
python3 -m pip install pygame
python3 game.py
```

## Controls

- `W/A/S/D` move
- `E` interact (farm plot, NPC, or zone action)
- `Q` cycle selected seed
- `F` quick action in mine/river (mine/fish)
- `C` craft Trail Ration
- `R` eat Trail Ration (restore stamina)
- `T` advance time segment (Morning → Afternoon → Evening → Night → next day)
- `X` sell produce/resources
- `ESC` quit

## Tests

```bash
python3 -m pytest -q
```

## Notes on originality

This project intentionally uses an original setting (**Emberbrook / Skyshard Valley**), original crop names, original NPC cast, original lore and progression beats, and a custom top-down world layout.
