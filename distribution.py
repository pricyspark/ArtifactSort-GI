import math
import numpy as np
from artifact import Artifact
import matplotlib as mpl
import matplotlib.pyplot as plt
import statistics
import copy
import matplotlib.pyplot as plt
from itertools import combinations, combinations_with_replacement, product, permutations
import random
import math

NUM_2_STAT = ['hp', 'atk', 'def', 'hp_', 'atk_', 'def_', 'enerRech_', 'eleMas', 
              'critRate_', 'critDMG_', 'pyro_dmg_', 'electro_dmg_', 'cryo_dmg_', 
              'hydro_dmg_', 'dendro_dmg_', 'anemo_dmg_', 'geo_dmg_', 
              'physical_dmg_', 'heal_']
STAT_2_NUM = {stat: index for index, stat in enumerate(NUM_2_STAT)}

CACHE_SIZE = 2000
MAIN_PROBS = {
    'flower' : {'hp': 1},
    'plume'  : {'atk': 1},
    'sands'  : {'hp_': 8/30,
                'atk_': 8/30,
                'def_': 8/30,
                'enerRech_': 3/30,
                'eleMas': 3/30},
    'goblet' : {'hp_': 77/400,
                'atk_': 77/400,
                'def_': 76/400,
                'pyro_dmg_': 20/400,
                'electro_dmg_': 20/400,
                'cryo_dmg_': 20/400,
                'hydro_dmg_': 20/400,
                'dendro_dmg_': 20/400,
                'anemo_dmg_': 20/400,
                'geo_dmg_': 20/400,
                'physical_dmg_': 20/400,
                'eleMas': 10/400},
    'circlet': {'hp_': 11/50,
                'atk_': 11/50,
                'def_': 11/50,
                'critRate_': 5/50,
                'critDMG_': 5/50,
                'heal_': 5/50,
                'eleMas': 2/50}
}
SUB_PROBS = [6, 6, 6, 4, 4, 4, 4, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def upgrades():
    coefs = (7, 8, 9, 10)
    bases = product(coefs, repeat=4)
    dictionary = {}
    num = 0
    for base in bases:
        distro = list(product(range(16), repeat=4)) + list(product(range(16), repeat=5))
        for upgrades in distro:
            if len(upgrades) == 4:
                prob = 0.8 * ((1/16) ** 4 / 256)
            else:
                prob = 0.2 * ((1/16) ** 5 / 256)

            substats = list(base)
            for upgrade in upgrades:
                substats[upgrade // 4] += coefs[upgrade % 4]
                
            substats = tuple(substats)
            if substats in dictionary:
                dictionary[substats] += prob
            else:
                dictionary[substats] = prob
        print(base)

    substats = np.zeros((len(dictionary), 4), dtype=np.int8)
    probs = np.zeros(len(dictionary), dtype=float)
    for idx, (substat, prob) in enumerate(dictionary.items()):
        substats[idx, :] = substat
        probs[idx] = prob

    #np.save('asdf', substats)
    #np.save('asdf', probs)

def base(slot):
    for stat in MAIN_PROBS[slot].keys():

        copy_SUB_PROBS = np.array(SUB_PROBS, dtype=float)
        if stat not in STAT_2_NUM:
            raise KeyError
        print('asdf', copy_SUB_PROBS[STAT_2_NUM[stat]])
        print(stat)
        copy_SUB_PROBS[STAT_2_NUM[stat]] = 0
        copy_SUB_PROBS /= np.sum(copy_SUB_PROBS)
        print(copy_SUB_PROBS)
        print(np.sum(copy_SUB_PROBS))

        sum = 0
        p = copy_SUB_PROBS
        qwer = {}
        for comb in permutations(range(10), 4):
            prob = 1
            total_prob = 0
            #asdf = (p[comb[0]] 
            #        * (p[comb[1]] / (1 - p[comb[0]])) 
            #        * (p[comb[2]] / (1 - p[comb[0]] - p[comb[1]]))
            #        * (p[comb[3]] / (1 - p[comb[0]] - p[comb[1]] - p[comb[2]])))
            for idx in comb:
                current_prob = copy_SUB_PROBS[idx] / (1 - total_prob)
                total_prob += copy_SUB_PROBS[idx]
                prob *= current_prob

            if prob == 0:
                continue
            
            comb = tuple(sorted(comb))
            if comb in qwer:
                qwer[comb] += prob
            else:
                qwer[comb] = prob

            sum += prob

            #print(prob)

            bases = product((0.7, 0.8, 0.9, 1.0), repeat=4)
            
        #    for upgrades in combinations_with_replacement(range(16), 4):

        print(sum)
        qwertyui = np.zeros((len(qwer), 5))

        for idx, (key, value) in enumerate(qwer.items()):
            qwertyui[idx, :-1] = key
            qwertyui[idx, -1] = value
        np.save(f'temp/{slot}_{stat}.npy', qwertyui)

base('circlet')