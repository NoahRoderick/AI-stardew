from game import CROPS, GameState


def test_farming_growth_and_harvest():
    game = GameState()
    plot_pos = (2, 2)
    game.selected_seed = "glowturnip"
    game.player.pos = plot_pos
    game.interact()  # plant
    for _ in range(CROPS["glowturnip"].growth_days):
        game.player.pos = plot_pos
        game.interact()  # water
        game.end_day()
    game.player.pos = plot_pos
    game.interact()  # harvest
    assert game.player.inventory["Glowturnip"] == 1


def test_bond_progression_restores_shrine():
    game = GameState()
    for npc in game.npcs.values():
        game.player.inventory[npc.likes] = 20

    for pos in game.npcs.keys():
        for _ in range(8):
            game.player.pos = pos
            game.interact()

    assert game.story_flags["shrine_restored"] is True
    assert game.player.max_stamina == 120


def test_season_rollover_withers_crops():
    game = GameState()
    plot_pos = (2, 2)
    game.selected_seed = "glowturnip"
    game.player.pos = plot_pos
    game.interact()  # plant spring crop
    game.day = 28
    game.time_segment = 3
    game.end_segment()  # force day->season rollover
    assert game.season == "Suncrest"
    assert game.farm[plot_pos].crop_key is None
