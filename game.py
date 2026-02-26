from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

try:
    import pygame
except ImportError:  # pragma: no cover - handled at runtime
    pygame = None

TILE_SIZE = 32
WORLD_W = 28
WORLD_H = 18
HUD_H = 96
SCREEN_W = WORLD_W * TILE_SIZE
SCREEN_H = WORLD_H * TILE_SIZE + HUD_H
FPS = 60

SEASONS = ["Dawnspring", "Suncrest", "Amberfall", "Frostwane"]


class Zone(str, Enum):
    FARM = "farm"
    MINE = "mine"
    RIVER = "river"
    TOWN = "town"


@dataclass
class CropType:
    key: str
    name: str
    season: str
    growth_days: int
    seed_price: int
    sell_price: int


CROPS: Dict[str, CropType] = {
    "glowturnip": CropType("glowturnip", "Glowturnip", "Dawnspring", 3, 18, 45),
    "sunberry": CropType("sunberry", "Sunberry", "Suncrest", 4, 26, 62),
    "coppercorn": CropType("coppercorn", "Coppercorn", "Amberfall", 3, 22, 54),
    "snowpea": CropType("snowpea", "Snowpea", "Frostwane", 2, 20, 42),
}


@dataclass
class Plot:
    crop_key: Optional[str] = None
    watered: bool = False
    growth: int = 0


@dataclass
class NPC:
    name: str
    likes: str
    bond: int = 0
    dialogue: str = ""


@dataclass
class PlayerState:
    pos: Tuple[int, int] = (8, 8)
    gold: int = 140
    stamina: int = 100
    max_stamina: int = 100
    inventory: Dict[str, int] = field(
        default_factory=lambda: {
            "Glowturnip Seeds": 4,
            "Sunberry Seeds": 2,
            "Coppercorn Seeds": 2,
            "Snowpea Seeds": 2,
            "Stone": 0,
            "Copper Ore": 0,
            "River Fish": 0,
            "Forest Fish": 0,
            "Glowturnip": 0,
            "Sunberry": 0,
            "Coppercorn": 0,
            "Snowpea": 0,
            "Trail Ration": 1,
        }
    )


class GameState:
    def __init__(self) -> None:
        self.player = PlayerState()
        self.day = 1
        self.year = 1
        self.season_idx = 0
        self.time_segment = 0
        self.selected_seed = "glowturnip"
        self.message = "Welcome to Emberbrook. Grow, explore, and restore the Sky Shrine."
        self.farm = {(x, y): Plot() for x in range(2, 11) for y in range(2, 8)}
        self.npcs = {
            (20, 4): NPC("Iri", "River Fish", dialogue="The river whispers when storms come."),
            (22, 6): NPC("Tomas", "Copper Ore", dialogue="The mine walls sing if you listen."),
            (19, 8): NPC("Sel", "Glowturnip", dialogue="Lantern petals glow brighter at dusk."),
        }
        self.story_flags = {"mine_unlocked": False, "festival_done": False, "shrine_restored": False}

    @property
    def season(self) -> str:
        return SEASONS[self.season_idx]

    def can_spend(self, amount: int) -> bool:
        return self.player.stamina >= amount

    def spend(self, amount: int) -> bool:
        if self.player.stamina < amount:
            self.message = "Too exhausted. End the day or eat a ration."
            return False
        self.player.stamina -= amount
        return True

    def move_player(self, dx: int, dy: int) -> None:
        x, y = self.player.pos
        nx, ny = max(0, min(WORLD_W - 1, x + dx)), max(0, min(WORLD_H - 1, y + dy))
        self.player.pos = (nx, ny)

    def interact(self) -> None:
        x, y = self.player.pos
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x, y)]

        for p in candidates:
            if p in self.npcs:
                self.talk(p)
                return
        for p in candidates:
            if p in self.farm:
                self.farm_action(p)
                return

        zone = self.current_zone()
        if zone == Zone.MINE:
            self.mine()
        elif zone == Zone.RIVER:
            self.fish()
        else:
            self.message = "Nothing to interact with here."

    def current_zone(self) -> Zone:
        x, y = self.player.pos
        if x <= 12 and y <= 10:
            return Zone.FARM
        if x >= 24 and y <= 7:
            return Zone.MINE
        if y >= 13:
            return Zone.RIVER
        return Zone.TOWN

    def farm_action(self, pos: Tuple[int, int]) -> None:
        plot = self.farm[pos]
        if plot.crop_key is None:
            crop = CROPS[self.selected_seed]
            seed_name = f"{crop.name} Seeds"
            if crop.season != self.season:
                self.message = f"{crop.name} grows in {crop.season}."
                return
            if self.player.inventory.get(seed_name, 0) <= 0:
                self.message = f"No {seed_name}. Buy or craft more later."
                return
            if not self.spend(2):
                return
            plot.crop_key = crop.key
            plot.growth = 0
            plot.watered = False
            self.player.inventory[seed_name] -= 1
            self.message = f"Planted {crop.name}."
        else:
            crop = CROPS[plot.crop_key]
            if plot.growth >= crop.growth_days:
                self.player.inventory[crop.name] += 1
                plot.crop_key = None
                plot.growth = 0
                plot.watered = False
                self.message = f"Harvested {crop.name}!"
            elif not plot.watered:
                if not self.spend(1):
                    return
                plot.watered = True
                self.message = "Watered crop."
            else:
                self.message = f"{crop.name} is still growing ({plot.growth}/{crop.growth_days})."

    def talk(self, npc_pos: Tuple[int, int]) -> None:
        npc = self.npcs[npc_pos]
        gain = 2
        if self.player.inventory.get(npc.likes, 0) > 0:
            self.player.inventory[npc.likes] -= 1
            gain += 4
        npc.bond = min(100, npc.bond + gain)
        self.message = f"{npc.name}: '{npc.dialogue}' Bond +{gain}"
        self._check_shrine_restore()

    def mine(self) -> None:
        if self.day < 3 and not self.story_flags["mine_unlocked"]:
            self.message = "Mine opens on day 3 after inspection."
            return
        self.story_flags["mine_unlocked"] = True
        if not self.spend(14):
            return
        ore = random.randint(1, 3)
        stone = random.randint(1, 4)
        self.player.inventory["Copper Ore"] += ore
        self.player.inventory["Stone"] += stone
        self.player.gold += ore * 3
        self.message = f"Mined {ore} ore and {stone} stone."

    def fish(self) -> None:
        if not self.spend(10):
            return
        if random.random() < 0.72:
            key = "River Fish" if random.random() < 0.65 else "Forest Fish"
            amount = random.randint(1, 2)
            self.player.inventory[key] += amount
            self.message = f"Caught {amount} {key}."
        else:
            self.message = "No catch this time."

    def craft_ration(self) -> None:
        if self.player.inventory["River Fish"] >= 1 and self.player.inventory["Forest Fish"] >= 1:
            self.player.inventory["River Fish"] -= 1
            self.player.inventory["Forest Fish"] -= 1
            self.player.inventory["Trail Ration"] += 1
            self.message = "Crafted Trail Ration."
        else:
            self.message = "Need 1 River Fish + 1 Forest Fish."

    def eat_ration(self) -> None:
        if self.player.inventory["Trail Ration"] <= 0:
            self.message = "No Trail Ration available."
            return
        self.player.inventory["Trail Ration"] -= 1
        self.player.stamina = min(self.player.max_stamina, self.player.stamina + 30)
        self.message = "A warm meal restores stamina."

    def sell_bin(self) -> None:
        prices = {
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
        for item, price in prices.items():
            qty = self.player.inventory.get(item, 0)
            if qty > 0:
                total += qty * price
                self.player.inventory[item] = 0
        self.player.gold += total
        self.message = f"Sold produce and loot for {total}g."

    def next_seed(self) -> None:
        keys = list(CROPS.keys())
        idx = (keys.index(self.selected_seed) + 1) % len(keys)
        self.selected_seed = keys[idx]
        self.message = f"Selected seed: {CROPS[self.selected_seed].name}."

    def end_segment(self) -> None:
        self.time_segment += 1
        if self.time_segment > 3:
            self.time_segment = 0
            self.end_day()
            return
        self.message = "Time passes..."

    def end_day(self) -> None:
        self.day += 1
        self.player.stamina = self.player.max_stamina
        for plot in self.farm.values():
            if plot.crop_key and plot.watered:
                plot.growth += 1
            plot.watered = False
        if self.day > 28:
            self.day = 1
            self.season_idx = (self.season_idx + 1) % len(SEASONS)
            if self.season_idx == 0:
                self.year += 1
            self._wither_out_of_season()
        self._check_festival()
        self.message = f"A new day begins. {self.season} Day {self.day}."

    def _wither_out_of_season(self) -> None:
        for plot in self.farm.values():
            if plot.crop_key and CROPS[plot.crop_key].season != self.season:
                plot.crop_key = None
                plot.growth = 0
                plot.watered = False

    def _check_festival(self) -> None:
        if self.season == "Dawnspring" and self.day == 14 and not self.story_flags["festival_done"]:
            self.story_flags["festival_done"] = True
            self.player.gold += 120
            self.message = "Lantern Bloom Festival reward: +120g!"

    def _check_shrine_restore(self) -> None:
        avg = sum(n.bond for n in self.npcs.values()) / len(self.npcs)
        if avg >= 45 and not self.story_flags["shrine_restored"]:
            self.story_flags["shrine_restored"] = True
            self.player.max_stamina += 20
            self.player.stamina = self.player.max_stamina
            self.message = "The Sky Shrine glows again! Max stamina +20."


class SpriteBank:
    def __init__(self) -> None:
        self.player_walk = self._player_frames()
        self.player_idle = self.player_walk[0]
        self.npc = self._npc_frame()
        self.water_anim = self._water_frames()

    def _player_frames(self) -> List[pygame.Surface]:
        frames: List[pygame.Surface] = []
        for step in range(4):
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf, (40, 62, 130), (8, 5, 16, 10))
            pygame.draw.rect(surf, (250, 212, 130), (10, 14, 12, 10))
            leg_y = 24 if step % 2 == 0 else 23
            pygame.draw.rect(surf, (60, 80, 160), (10, leg_y, 4, 8))
            pygame.draw.rect(surf, (60, 80, 160), (18, 31 - leg_y + 23, 4, 8))
            frames.append(surf)
        return frames

    def _npc_frame(self) -> pygame.Surface:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(surf, (244, 203, 155), (16, 10), 6)
        pygame.draw.rect(surf, (149, 84, 159), (10, 16, 12, 12))
        return surf

    def _water_frames(self) -> List[pygame.Surface]:
        frames: List[pygame.Surface] = []
        shades = [(61, 121, 185), (70, 136, 201), (52, 110, 170)]
        for c in shades:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill(c)
            pygame.draw.line(surf, (192, 231, 255), (3, 8), (27, 8), 2)
            pygame.draw.line(surf, (192, 231, 255), (5, 20), (24, 20), 2)
            frames.append(surf)
        return frames


def draw(game: GameState, screen: pygame.Surface, font: pygame.font.Font, sprites: SpriteBank, tick: int) -> None:
    zone_colors = {
        Zone.FARM: (113, 168, 92),
        Zone.TOWN: (171, 153, 116),
        Zone.MINE: (100, 97, 109),
    }
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            zone = game.current_zone() if (x, y) == game.player.pos else (
                Zone.FARM if x <= 12 and y <= 10 else Zone.MINE if x >= 24 and y <= 7 else Zone.RIVER if y >= 13 else Zone.TOWN
            )
            if zone == Zone.RIVER:
                frame = sprites.water_anim[(tick // 25) % len(sprites.water_anim)]
                screen.blit(frame, (x * TILE_SIZE, y * TILE_SIZE))
            else:
                pygame.draw.rect(screen, zone_colors[zone], (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    for (x, y), plot in game.farm.items():
        r = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, (95, 67, 43), r.inflate(-2, -2))
        if plot.crop_key:
            crop = CROPS[plot.crop_key]
            stage = min(2, int((plot.growth / max(1, crop.growth_days)) * 3))
            h = [8, 14, 20][stage]
            color = (145, 247, 123) if crop.key in {"glowturnip", "snowpea"} else (255, 189, 84)
            pygame.draw.rect(screen, color, (r.x + 10, r.y + 22 - h, 12, h))
        if plot.watered:
            pygame.draw.circle(screen, (80, 143, 224), (r.x + 6, r.y + 26), 3)

    for (x, y), _npc in game.npcs.items():
        screen.blit(sprites.npc, (x * TILE_SIZE, y * TILE_SIZE))

    pframe = sprites.player_walk[(tick // 12) % len(sprites.player_walk)]
    screen.blit(pframe, (game.player.pos[0] * TILE_SIZE, game.player.pos[1] * TILE_SIZE))

    pygame.draw.rect(screen, (24, 24, 28), (0, WORLD_H * TILE_SIZE, SCREEN_W, HUD_H))
    hud = [
        f"Y{game.year} {game.season} D{game.day}  Segment:{['Morning','Afternoon','Evening','Night'][game.time_segment]}",
        f"Gold:{game.player.gold}  Stamina:{game.player.stamina}/{game.player.max_stamina}  Zone:{game.current_zone().value}",
        f"Seed:{CROPS[game.selected_seed].name}  Ration:{game.player.inventory['Trail Ration']}  Message: {game.message}",
        "WASD move | E interact | Q cycle seed | F fish/mine in zone | C craft ration | R eat | T end time | X sell | ESC quit",
    ]
    for i, line in enumerate(hud):
        screen.blit(font.render(line, True, (231, 231, 231)), (12, WORLD_H * TILE_SIZE + 6 + i * 22))


def run() -> None:
    if pygame is None:
        print("This version requires pygame. Install with: python3 -m pip install pygame")
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Emberbrook: Skyshard Valley")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    game = GameState()
    sprites = SpriteBank()

    running = True
    tick = 0
    while running:
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    game.move_player(0, -1)
                elif event.key == pygame.K_s:
                    game.move_player(0, 1)
                elif event.key == pygame.K_a:
                    game.move_player(-1, 0)
                elif event.key == pygame.K_d:
                    game.move_player(1, 0)
                elif event.key == pygame.K_e:
                    game.interact()
                elif event.key == pygame.K_q:
                    game.next_seed()
                elif event.key == pygame.K_f:
                    if game.current_zone() == Zone.MINE:
                        game.mine()
                    elif game.current_zone() == Zone.RIVER:
                        game.fish()
                    else:
                        game.message = "Use F at the river or mine."
                elif event.key == pygame.K_c:
                    game.craft_ration()
                elif event.key == pygame.K_r:
                    game.eat_ration()
                elif event.key == pygame.K_t:
                    game.end_segment()
                elif event.key == pygame.K_x:
                    game.sell_bin()

        draw(game, screen, font, sprites, tick)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
