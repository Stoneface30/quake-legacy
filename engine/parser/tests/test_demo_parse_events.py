

def test_missile_events_are_named_in_the_launcher_space_not_means_of_death():
    """Entity-sourced missile_hit/miss carry the missile's s.weapon (WP_*).
    Obituaries carry MOD_*. The two tables disagree exactly where it hurts."""
    import demo_parse as dp
    assert dp._WP_NAMES[4] == 'GRENADE_LAUNCHER' and dp._MOD_NAMES[4] == 'GRENADE'
    assert dp._WP_NAMES[5] == 'ROCKET_LAUNCHER' and dp._MOD_NAMES[5] == 'GRENADE_SPLASH'
    assert dp._WP_NAMES[8] == 'PLASMAGUN'
    src = open(dp.__file__, encoding='utf-8').read()
    branch = src[src.index('_EV_MISSILE_MISS, _EV_GIB_PLAYER):'):][:900]
    assert "_WP_NAMES.get(ev['weapon']" in branch
