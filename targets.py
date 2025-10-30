# Universal sets use all available targets.
# DPS sets always scale CRIT. All non-CRIT hits ignore DMG bonus
# anyways, so they wouldn't be considered for optimization. Also ignore
# healing.

# Super paranoid targets for extremely specialized stats. Probably don't
# use though, since a since stat target doesn't have enough degrees of
# freedom to differentiate artifacts well.
SCHIZO_TARGETS = {
    'flower': (
        {'hp_': 6, 'hp': 2},
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2},
        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2},
        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        
        {'enerRech_': 1},
        {'eleMas': 1},
        {'crit_': 1}
    ),
    'plume': (
        {'hp_': 6, 'hp': 2},
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2},
        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2},
        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        
        {'enerRech_': 1},
        {'eleMas': 1},
        {'crit_': 1}
    ),
    'sands': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'goblet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'circlet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
        
        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
    )
}

ALL_TARGETS = {
    'flower': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'plume': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'sands': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'goblet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'circlet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
        
        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
    )
}

DPS_TARGETS = {
    'flower': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'plume': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'sands': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'goblet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    ),
    'circlet': (
        {'hp_': 6, 'hp': 2, 'crit_': 8},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'atk_': 6, 'atk': 2, 'crit_': 8},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

        {'def_': 6, 'def': 2, 'crit_': 8},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
    )
}

HEAL_TARGETS = {
    'flower': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'plume': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'sands': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'goblet': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'circlet': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

        {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
    )
}

SUPPORT_TARGETS = {
    'flower': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'plume': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'sands': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'goblet': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    ),
    'circlet': (
        {'hp_': 6, 'hp': 2, 'enerRech_': 10},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
        {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

        {'atk_': 6, 'atk': 2, 'enerRech_': 10},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
        {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

        {'def_': 6, 'def': 2, 'enerRech_': 10},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
        {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
    )
}

SET_TARGETS = {
    # Some niche supports use 4p to teamwide buff, making this universal
    'ArchaicPetra': ALL_TARGETS,

    # Cryo and CRIT DPS set 
    'BlizzardStrayer': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # The 4p is unique, so there is a chance a non-Physical character
    # will need the 4p so badly that they still use this.
    'BloodstainedChivalry': ALL_TARGETS,

    # Pyro DPS set
    'CrimsonWitchOfFlames': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # Dendro support/sub-DPS set. Some non-Dendro characters can run
    # this, so universal, but they don't care about DMG
    'DeepwoodMemories': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
        )
    },

    # Anemo DPS set. The 4p is not strong to warrant a non-Anemo using
    # it.
    'DesertPavilionChronicle': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # ATK DPS set
    'EchoesOfAnOffering': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # ER general set
    'EmblemOfSeveredFate': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
        )
    },

    # Literally only ever Skirk. But to be safe, treat this as a Cryo
    # DPS set that ignores ER
    'FinaleOfTheDeepGalleries': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7}
        )
    },

    # EM support and heal set. TODO: maybe remove heal
    'FlowerOfParadiseLost': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
        )
    },

    # ATK DMG set
    'FragmentOfHarmonicWhimsy': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # EM general set
    'GildedDreams': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10}
        )
    },

    # ATK DMG set. 4p set doesn't specify ATK, but it's not strong
    # enough to warrant a non-ATK scaler using it. Mostly used for the
    # ATK 2p.
    'GladiatorsFinale': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # Sub-DPS set
    'GoldenTroupe': DPS_TARGETS,

    # Hydro DPS set
    'HeartOfDepth': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # DEF Geo DPS set TODO maybe get rid of EM
    'HuskOfOpulentDreams': {
        'flower': (
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # DPS set. Technically anyone can use this equally well as long as
    # the enemy has pyro.
    'Lavawalker': DPS_TARGETS,

    # Plunge DPS set
    'LongNightsOath': DPS_TARGETS,

    # Heal set
    'MaidenBeloved': HEAL_TARGETS,

    # DPS set
    'MarechausseeHunter': DPS_TARGETS,
    
    # EM DPS set
    'NightOfTheSkysUnveiling': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # ER general set (same as Emblem)
    'NoblesseOblige': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'hp_': 6, 'hp': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'atk_': 6, 'atk': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
            
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 6, 'eleMas': 16, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 7, 'heal_': 10},
            {'def_': 6, 'def': 2, 'enerRech_': 10, 'eleMas': 16, 'heal_': 10},
        )
    },

    # ATK Hydro DPS set
    'NymphsDream': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # DPS set
    'ObsidianCodex': DPS_TARGETS,

    # Heal set
    'OceanHuedClam': HEAL_TARGETS,

    # ATK Physical DPS set
    'PaleFlame': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # Universal set. 4p is DPS, 2p is support TODO maybe make it more
    # specific, since it probably won't heal
    'RetracingBolide': ALL_TARGETS,

    # Universal set. 4p is so good that even DMG oriented characters may
    # use it.
    'ScrollOfTheHeroOfCinderCity': ALL_TARGETS,
    
    # Universal set. TODO check this
    'SilkenMoonsSerenade': ALL_TARGETS,

    # DPS set
    'ShimenawasReminiscence': DPS_TARGETS,

    # Heal set
    'SongOfDaysPast': HEAL_TARGETS,

    # Universal set. TODO check this it's weird and niche
    'TenacityOfTheMillelith': ALL_TARGETS,

    # Electro DPS set
    'ThunderingFury': {
        'flower': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'hp_': 6, 'hp': 2, 'crit_': 8},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'eleMas': 7},
            {'hp_': 6, 'hp': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},

            {'def_': 6, 'def': 2, 'crit_': 8},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10},
            {'def_': 6, 'def': 2, 'crit_': 8, 'eleMas': 7},
            {'def_': 6, 'def': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # DPS set. Technically anyone can use this equally well as long as
    # the enemy has electro.
    'Thundersoother': DPS_TARGETS,

    # DPS set. 2p adds ATK, but the 4p is unique and maybe trong enough
    # for a non-ATK character to use it.
    'UnfinishedReverie': DPS_TARGETS,

    # ATK DPS set.
    'VermillionHereafter': {
        'flower': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'plume': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'sands': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'goblet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'pyro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'electro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'cryo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'hydro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'dendro_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'anemo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'geo_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'physical_dmg_': 8, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        ),
        'circlet': (
            {'atk_': 6, 'atk': 2, 'crit_': 8},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'eleMas': 7},
            {'atk_': 6, 'atk': 2, 'crit_': 8, 'enerRech_': 10, 'eleMas': 7}
        )
    },

    # Universal set.
    'ViridescentVenerer': ALL_TARGETS,

    # DPS set. 4p is universal and strong, but niche. The 2p probably
    # doesn't require specialized min-maxing, because any character that
    # only cares about HP will have a cutoff, like Nilou. Granted,
    # Nilou's cutoff isn't reachable without Key of Khaj Nisut, but for
    # now I think the effort of heavily min-maxing raw HP isn't worth
    # it. TODO idfk what I was saying here
    'VourukashasGlow': DPS_TARGETS,

    # DPS set
    'WanderersTroupe': DPS_TARGETS
}