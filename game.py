from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

SEASONS = ["Dawnspring", "Suncrest", "Amberfall", "Frostwane"]
TIMES_OF_DAY = ["Morning", "Afternoon", "Evening", "Night"]


@dataclass
class CropType:
    name: str
    season: str
    growth_days: int
    seed_price: int
    sell_price: int


CROPS: Dict[str, CropType] = {
    "glowturnip": CropType("Glowturnip", "Dawnspring", 3, 18, 42),
    "sunberry": CropType("Sunberry", "Suncrest", 4, 26, 58),
    "coppercorn": CropType("Coppercorn", "Amberfall", 3, 22, 50),
    "snowpea": CropType("Snowpea", "Frostwane", 2, 20, 40),
}


@dataclass
class Plot:
    crop_key: Optional[str] = None
    watered: bool = False
    days_grown: int = 0


@dataclass
class NPC:
    name: str
    likes: str
    bond: int = 0


@dataclass
class Player:
    name: str
    gold: int = 120
    stamina: int = 100
    max_stamina: int = 100
    inventory: Dict[str, int] = field(default_factory=lambda: {
        "Stone": 0,
        "Copper Ore": 0,
        "River Fish": 0,
        "Forest Fish": 0,
        "Glowturnip": 0,
        "Sunberry": 0,
        "Coppercorn": 0,
        "Snowpea": 0,
        "Trail Ration": 1,
        "Lure": 1,
        "Lantern Charm": 0,
    })


class EmberbrookGame:
    def __init__(self, player_name: str) -> None:
        self.player = Player(player_name)
        self.day = 1
        self.year = 1
        self.season_index = 0
        self.time_index = 0
        self.story_flags: Dict[str, bool] = {
            "opened_mine": False,
            "joined_festival": False,
            "restored_shrine": False,
        }
        self.farm: List[Plot] = [Plot() for _ in range(12)]
        self.npcs = {
            "Iri": NPC("Iri", "River Fish"),
            "Tomas": NPC("Tomas", "Copper Ore"),
            "Sel": NPC("Sel", "Glowturnip"),
        }
        self.recipes = {
            "Trail Ration": {"River Fish": 1, "Forest Fish": 1},
            "Lantern Charm": {"Stone": 5, "Copper Ore": 3},
        }

    @property
    def season(self) -> str:
        return SEASONS[self.season_index]

    @property
    def time_of_day(self) -> str:
        return TIMES_OF_DAY[self.time_index]

    def _spend_stamina(self, amount: int) -> bool:
        if self.player.stamina < amount:
            print("You are too tired. Eat, sleep, or choose a lighter task.")
            return False
        self.player.stamina -= amount
        return True

    def plant_crop(self, crop_key: str, plot_index: int) -> None:
        crop = CROPS.get(crop_key)
        if not crop:
            print("Unknown seed.")
            return
        if crop.season != self.season:
            print(f"{crop.name} only grows in {crop.season}.")
            return
        if self.player.gold < crop.seed_price:
            print("Not enough gold.")
            return
        if not (0 <= plot_index < len(self.farm)):
            print("Invalid plot index.")
            return
        plot = self.farm[plot_index]
        if plot.crop_key is not None:
            print("Plot already occupied.")
            return

        self.player.gold -= crop.seed_price
        plot.crop_key = crop_key
        plot.days_grown = 0
        plot.watered = False
        print(f"Planted {crop.name} in plot {plot_index}.")

    def water_all(self) -> None:
        water_cost = sum(1 for p in self.farm if p.crop_key is not None and not p.watered)
        if water_cost == 0:
            print("No thirsty crops right now.")
            return
        if not self._spend_stamina(water_cost * 2):
            return
        for plot in self.farm:
            if plot.crop_key is not None:
                plot.watered = True
        print(f"Watered crops. Stamina -{water_cost * 2}.")

    def harvest_ready(self) -> None:
        harvested = 0
        for plot in self.farm:
            if not plot.crop_key:
                continue
            crop = CROPS[plot.crop_key]
            if plot.days_grown >= crop.growth_days:
                self.player.inventory[crop.name] = self.player.inventory.get(crop.name, 0) + 1
                plot.crop_key = None
                plot.days_grown = 0
                plot.watered = False
                harvested += 1
        if harvested:
            print(f"Harvested {harvested} crops.")
        else:
            print("Nothing is ready yet.")

    def go_mining(self) -> None:
        if not self.story_flags["opened_mine"] and self.day < 4:
            print("The Crystal Hollow Mine opens on day 4 after safety checks.")
            return
        self.story_flags["opened_mine"] = True
        if not self._spend_stamina(18):
            return
        ore = random.randint(1, 4)
        stone = random.randint(2, 6)
        self.player.inventory["Copper Ore"] += ore
        self.player.inventory["Stone"] += stone
        self.player.gold += ore * 4
        print(f"Mined {ore} Copper Ore and {stone} Stone.")

    def go_fishing(self, area: str = "river") -> None:
        if not self._spend_stamina(12):
            return
        base_chance = 0.65
        if self.player.inventory["Lure"] > 0:
            base_chance += 0.10
        if random.random() <= base_chance:
            key = "River Fish" if area == "river" else "Forest Fish"
            amount = random.randint(1, 2)
            self.player.inventory[key] += amount
            self.player.gold += amount * 6
            print(f"Caught {amount} {key}.")
        else:
            print("No bites this time.")

    def craft(self, item_name: str) -> None:
        recipe = self.recipes.get(item_name)
        if not recipe:
            print("Unknown recipe.")
            return
        for ingredient, amount in recipe.items():
            if self.player.inventory.get(ingredient, 0) < amount:
                print(f"Missing {ingredient}.")
                return
        for ingredient, amount in recipe.items():
            self.player.inventory[ingredient] -= amount
        self.player.inventory[item_name] = self.player.inventory.get(item_name, 0) + 1
        print(f"Crafted {item_name}.")

    def talk(self, npc_name: str, gift: Optional[str] = None) -> None:
        npc = self.npcs.get(npc_name)
        if not npc:
            print("No such villager.")
            return
        increase = 2
        if gift:
            if self.player.inventory.get(gift, 0) <= 0:
                print(f"You don't have {gift}.")
                return
            self.player.inventory[gift] -= 1
            increase += 4 if gift == npc.likes else 1
        npc.bond = min(100, npc.bond + increase)
        print(f"Bond with {npc.name} is now {npc.bond}.")

    def sell_inventory(self) -> None:
        values = {
            "River Fish": 10,
            "Forest Fish": 12,
            "Glowturnip": 45,
            "Sunberry": 62,
            "Coppercorn": 54,
            "Snowpea": 42,
            "Copper Ore": 9,
            "Stone": 2,
        }
        total = 0
        for item, price in values.items():
            qty = self.player.inventory.get(item, 0)
            if qty > 0:
                total += qty * price
                self.player.inventory[item] = 0
        self.player.gold += total
        print(f"Sold goods for {total} gold.")

    def end_time_segment(self) -> None:
        self.time_index += 1
        if self.time_index >= len(TIMES_OF_DAY):
            self.end_day()

    def end_day(self) -> None:
        self.time_index = 0
        self.day += 1
        self.player.stamina = self.player.max_stamina

        for plot in self.farm:
            if plot.crop_key and plot.watered:
                plot.days_grown += 1
            plot.watered = False

        if self.day > 28:
            self.day = 1
            self.season_index += 1
            if self.season_index >= len(SEASONS):
                self.season_index = 0
                self.year += 1
            self._wither_out_of_season_crops()

        self._handle_seasonal_events()

    def _wither_out_of_season_crops(self) -> None:
        for plot in self.farm:
            if not plot.crop_key:
                continue
            crop = CROPS[plot.crop_key]
            if crop.season != self.season:
                plot.crop_key = None
                plot.days_grown = 0
                plot.watered = False

    def _handle_seasonal_events(self) -> None:
        if self.season == "Dawnspring" and self.day == 14 and not self.story_flags["joined_festival"]:
            self.story_flags["joined_festival"] = True
            self.player.gold += 120
            print("You won second place at the Lantern Bloom Festival! +120 gold")

        avg_bond = sum(n.bond for n in self.npcs.values()) / len(self.npcs)
        if avg_bond >= 45 and not self.story_flags["restored_shrine"]:
            self.story_flags["restored_shrine"] = True
            self.player.max_stamina += 20
            self.player.stamina = self.player.max_stamina
            print("Together with the village, you restored the hill shrine. Max stamina +20!")

    def status(self) -> str:
        planted = sum(1 for p in self.farm if p.crop_key)
        ready = sum(1 for p in self.farm if p.crop_key and CROPS[p.crop_key].growth_days <= p.days_grown)
        bonds = ", ".join(f"{n.name}:{n.bond}" for n in self.npcs.values())
        return (
            f"Year {self.year} | {self.season} Day {self.day} {self.time_of_day}\n"
            f"Gold: {self.player.gold} | Stamina: {self.player.stamina}/{self.player.max_stamina}\n"
            f"Farm plots in use: {planted}/12 (Ready: {ready})\n"
            f"Bonds -> {bonds}"
        )


def print_help() -> None:
    print(
        """\
Commands:
  status
  plant <crop_key> <plot_index>   (crop keys: glowturnip, sunberry, coppercorn, snowpea)
  water
  harvest
  mine
  fish [river|forest]
  craft <item_name>
  talk <npc_name> [gift_item]
  sell
  end      (advance time segment)
  help
  quit
"""
    )


def main() -> None:
    print("Welcome to Emberbrook: Echoes of the Vale")
    name = input("Name your character: ").strip() or "Wren"
    game = EmberbrookGame(name)

    intro = (
        "You inherited a weathered homestead above Emberbrook, a valley powered by old sky-lanterns. "
        "Rebuild the farm, earn trust, and uncover the shrine's forgotten engine."
    )
    print(intro)
    print_help()

    while True:
        print("\n" + game.status())
        cmd = input("> ").strip()
        if not cmd:
            continue
        parts = cmd.split()
        action = parts[0].lower()

        if action == "quit":
            print("Thanks for playing.")
            break
        if action == "help":
            print_help()
            continue
        if action == "status":
            continue
        if action == "plant" and len(parts) == 3:
            game.plant_crop(parts[1].lower(), int(parts[2]))
        elif action == "water":
            game.water_all()
        elif action == "harvest":
            game.harvest_ready()
        elif action == "mine":
            game.go_mining()
        elif action == "fish":
            area = parts[1].lower() if len(parts) > 1 else "river"
            game.go_fishing(area)
        elif action == "craft" and len(parts) >= 2:
            game.craft(" ".join(parts[1:]))
        elif action == "talk" and len(parts) >= 2:
            gift = " ".join(parts[2:]) if len(parts) > 2 else None
            game.talk(parts[1], gift)
        elif action == "sell":
            game.sell_inventory()
        elif action == "end":
            game.end_time_segment()
        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
