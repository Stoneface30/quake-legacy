"""PANTHEON — the engine. Quake, WolfcamQL and .dm_73 are backends.

    navigation   valid places to stand, mined from real play
    scenario     author a round as game intent
    compiler     intent -> the observed CA protocol grammar

Protocol values live at the compiler layer and below. Nothing that authors a
round should be able to name an entity field index.
"""
