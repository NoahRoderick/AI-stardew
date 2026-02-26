# Emberbrook: Echoes of the Vale

A cozy, progression-driven farming simulation RPG prototype inspired by the *genre pillars* of farm-life RPGs, with an original world, characters, and progression hooks.

## Core systems included

- **Crop farming** with seasonal seed restrictions, watering, growth timers, harvesting, and seasonal crop withering.
- **Mining** in Crystal Hollow for stone + ore with stamina costs.
- **Fishing** with river/forest spots and catch chance.
- **Crafting** from gathered resources (Trail Ration, Lantern Charm).
- **Relationship building** with three villagers (Iri, Tomas, Sel), favorite gifts, and bond progression.
- **Seasonal event** (Lantern Bloom Festival) and a **community progression milestone** (restoring the hill shrine).
- **Day-night cycle** across Morning / Afternoon / Evening / Night with sleep-driven day progression.
- **Original setting and narrative** centered on Emberbrook valley and an ancient sky-lantern shrine.

## Run

```bash
python3 game.py
```

## Test

```bash
python3 -m pytest -q
```

## Command quick reference

```text
status
plant <crop_key> <plot_index>
water
harvest
mine
fish [river|forest]
craft <item_name>
talk <npc_name> [gift_item]
sell
end
help
quit
```

Crop keys:
- `glowturnip` (Dawnspring)
- `sunberry` (Suncrest)
- `coppercorn` (Amberfall)
- `snowpea` (Frostwane)
