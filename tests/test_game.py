from game import EmberbrookGame, CROPS


def test_plant_water_grow_harvest_cycle():
    game = EmberbrookGame("Test")
    game.plant_crop("glowturnip", 0)
    assert game.farm[0].crop_key == "glowturnip"

    for _ in range(CROPS["glowturnip"].growth_days):
        game.water_all()
        game.end_day()

    game.harvest_ready()
    assert game.player.inventory["Glowturnip"] == 1
    assert game.farm[0].crop_key is None


def test_relationship_restores_shrine_bonus_stamina():
    game = EmberbrookGame("Test")
    for _ in range(10):
        game.player.inventory["River Fish"] += 1
        game.talk("Iri", "River Fish")
        game.player.inventory["Copper Ore"] += 1
        game.talk("Tomas", "Copper Ore")
        game.player.inventory["Glowturnip"] += 1
        game.talk("Sel", "Glowturnip")

    game._handle_seasonal_events()
    assert game.story_flags["restored_shrine"] is True
    assert game.player.max_stamina == 120


def test_season_rollover_withers_wrong_crops():
    game = EmberbrookGame("Test")
    game.plant_crop("glowturnip", 0)
    game.day = 28
    game.time_index = 3
    game.end_time_segment()
    assert game.season == "Suncrest"
    assert game.farm[0].crop_key is None
