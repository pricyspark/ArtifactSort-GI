import random
import math
import numpy as np
import copy
import json
import functools
from memory_profiler import profile
from numba import jit
from numba.experimental import jitclass
from collections.abc import Iterable
from pathlib import Path

def lru_cache_with_numpy(maxsize=128):
    """
    A decorator that caches function calls using functools.lru_cache.
    It handles functions with two arguments where the first is cacheable
    and the second is a NumPy array by converting the array into a hashable form.
    
    Parameters:
    - maxsize (int): The maximum size of the cache. Defaults to 128.
    
    Returns:
    - Decorated function with caching capability.
    """
    def decorator(func):
        # Define the cached helper function
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(arg1, dtype_str, shape, array_data):
            # Reconstruct the NumPy array from cached data
            dtype = np.dtype(dtype_str)
            array = np.frombuffer(array_data, dtype=dtype).reshape(shape)
            return func(arg1, array)
        
        @functools.wraps(func)
        def wrapper(arg1, array):
            if not isinstance(array, np.ndarray):
                raise TypeError("The second argument must be a NumPy array.")
            
            # Extract hashable components from the NumPy array
            dtype_str = array.dtype.str
            shape = array.shape
            array_data = array.tobytes()
            
            return cached_func(arg1, dtype_str, shape, array_data)
        
        return wrapper
    return decorator

def lru_cache_two_numpy(maxsize=128):
    """
    A decorator that caches function calls using functools.lru_cache.
    It handles functions with two NumPy array arguments by converting the arrays 
    into hashable forms (dtype, shape, and data bytes).

    Parameters:
    - maxsize (int): The maximum size of the cache. Defaults to 128.

    Returns:
    - Decorated function with caching capability.
    """
    def decorator(func):
        # Define the cached helper function
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(dtype_str1, shape1, array_data1,
                        dtype_str2, shape2, array_data2):
            # Reconstruct the first NumPy array from cached data
            dtype1 = np.dtype(dtype_str1)
            array1 = np.frombuffer(array_data1, dtype=dtype1).reshape(shape1)
            
            # Reconstruct the second NumPy array from cached data
            dtype2 = np.dtype(dtype_str2)
            array2 = np.frombuffer(array_data2, dtype=dtype2).reshape(shape2)
            
            return func(array1, array2)
        
        @functools.wraps(func)
        def wrapper(array1, array2):
            # Validate input types
            if not isinstance(array1, np.ndarray) or not isinstance(array2, np.ndarray):
                raise TypeError("Both arguments must be NumPy arrays.")
            
            # Extract hashable components from the first NumPy array
            dtype_str1 = array1.dtype.str
            shape1 = array1.shape
            array_data1 = array1.tobytes()
            
            # Extract hashable components from the second NumPy array
            dtype_str2 = array2.dtype.str
            shape2 = array2.shape
            array_data2 = array2.tobytes()
            
            return cached_func( dtype_str1, shape1, array_data1,
                                dtype_str2, shape2, array_data2 )
        
        return wrapper
    return decorator

def lru_cache_nested_numpy(maxsize=128):
    """
    A decorator that caches function calls using functools.lru_cache.
    It handles functions with parameters structured as ((numpy array, numpy array), numpy array)
    by converting each NumPy array into hashable forms (dtype, shape, and data bytes).

    Parameters:
    - maxsize (int): The maximum size of the cache. Defaults to 128.

    Returns:
    - Decorated function with caching capability.
    """
    def decorator(func):
        # Define the cached helper function
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(dtype_str1, shape1, array_data1,
                        dtype_str2, shape2, array_data2,
                        dtype_str3, shape3, array_data3):
            # Reconstruct the first NumPy array from cached data
            dtype1 = np.dtype(dtype_str1)
            array1 = np.frombuffer(array_data1, dtype=dtype1).reshape(shape1)
            
            # Reconstruct the second NumPy array from cached data
            dtype2 = np.dtype(dtype_str2)
            array2 = np.frombuffer(array_data2, dtype=dtype2).reshape(shape2)
            
            # Reconstruct the third NumPy array from cached data
            dtype3 = np.dtype(dtype_str3)
            array3 = np.frombuffer(array_data3, dtype=dtype3).reshape(shape3)
            
            return func((array1, array2), array3)
        
        @functools.wraps(func)
        def wrapper(pair, array3):
            # TODO: maybe put the safety checks back in, but thats slower
            # Validate input types
            #if not (isinstance(pair, tuple) and len(pair) == 2):
            #    raise TypeError("The first argument must be a tuple of two NumPy arrays.")
            array1, array2 = pair
            #if not isinstance(array1, np.ndarray) or not isinstance(array2, np.ndarray):
            #    raise TypeError("Both elements in the first tuple must be NumPy arrays.")
            #if not isinstance(array3, np.ndarray):
            #    raise TypeError("The second argument must be a NumPy array.")
            
            # Extract hashable components from the first NumPy array
            dtype_str1 = array1.dtype.str
            shape1 = array1.shape
            array_data1 = array1.tobytes()
            
            # Extract hashable components from the second NumPy array
            dtype_str2 = array2.dtype.str
            shape2 = array2.shape
            array_data2 = array2.tobytes()
            
            # Extract hashable components from the third NumPy array
            dtype_str3 = array3.dtype.str
            shape3 = array3.shape
            array_data3 = array3.tobytes()
            
            return cached_func( dtype_str1, shape1, array_data1,
                                dtype_str2, shape2, array_data2,
                                dtype_str3, shape3, array_data3 )
        
        return wrapper
    return decorator





# 0: hp
# 1: atk
# 2: def
# 3: hp_
# 4: atk_
# 5: def_
# 6: enerRech_
# 7: eleMas
# 8: critRate_
# 9: critDMG_
# 10: pyro_dmg_
# 11: electro_dmg_
# 12: cryo_dmg_
# 13: hydro_dmg_
# 14: dendro_dmg_
# 15: anemo_dmg_
# 16: geo_dmg_
# 17: physical_dmg_
# 18: heal_

FLOAT_DTYPE = np.float32

STATS = [
    'hp', 'atk', 'def', 'hp_', 'atk_', 'def_', 'enerRech_', 'eleMas', 
    'critRate_', 'critDMG_', 'pyro_dmg_', 'electro_dmg_', 'cryo_dmg_', 
    'hydro_dmg_', 'dendro_dmg_', 'anemo_dmg_', 'geo_dmg_', 'physical_dmg_', 
    'heal_'
]

STAT_2_NUM = {stat: index for index, stat in enumerate(STATS)}

CACHE_SIZE = 2000
MAIN_PROBS = {
    'flower' : {
        'hp': 1
    },
    'plume'  : {
        'atk': 1
    },
    'sands'  : {
        'hp_': 8/30,
        'atk_': 8/30,
        'def_': 8/30,
        'enerRech_': 3/30,
        'eleMas': 3/30
    },
    'goblet' : {
        'hp_': 77/400,
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
        'eleMas': 10/400
    },
    'circlet': {
        'hp_': 11/50,
        'atk_': 11/50,
        'def_': 11/50,
        'critRate_': 5/50,
        'critDMG_': 5/50,
        'heal_': 5/50,
        'eleMas': 2/50
    }
}

SUB_PROBS = [6, 6, 6, 4, 4, 4, 4, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0]

MAIN_VALUES = {
    'hp': 4780,
    'atk': 311,
    'hp_': 46.6,
    'atk_': 46.6,
    'def_': 58.3,
    'pyro_dmg_':  46.6,
    'electro_dmg_': 46.6,
    'cryo_dmg_': 46.6,
    'hydro_dmg_': 46.6,
    'dendro_dmg_': 46.6,
    'anemo_dmg_': 46.6,
    'geo_dmg_': 46.6,
    'physical_dmg_': 58.3,
    'enerRech_': 51.8,
    'eleMas': 186.5,
    'critRate_': 31.1,
    'critDMG_': 62.2,
    'heal_': 34.9
}

SUB_VALUES = {
    'hp': 298.75,
    'atk': 19.45,
    'def': 23.13,
    'hp_': 5.83,
    'atk_': 5.83,
    'def_': 7.29,
    'enerRech_': 6.48,
    'eleMas': 23.31,
    'critRate_': 3.89,
    'critDMG_': 7.77
}

ARTIFACT_REQ_EXP = [
    0,
    3000,
    6725,
    11150,
    16300,
    22200,
    28875,
    36375,
    44725,
    53950,
    64075,
    75125,
    87150,
    100175,
    115325,
    132925,
    153300,
    176800,
    203850,
    234900,
    270475
]

# Generate all possible counts of increments that sum to time_steps
def generate_permutations(total, count):
    if count == 1:
        yield [total]
    else:
        for i in range(total + 1):
            for tail in generate_permutations(total - i, count - 1):
                yield [i] + tail

# Calculate the probability for each permutation
def calculate_probability(counts, base_prob):
    numerator = math.factorial(sum(counts))
    denominator = 1
    for count in counts:
        denominator *= math.factorial(count)
    multinomial_coeff = numerator / denominator
    return multinomial_coeff * base_prob

class FastArtifact:
    score_cdfs = {}

    def __init__(self, set, lvl, slot, main=None, substats=None, stats=None, lock=False):

        self.set: str = set
        self.lvl: int = lvl
        self.slot: str = slot
        self.lock = lock

        if stats is not None:
            mask = stats == 16/3
            if np.any(mask):
                self.main = np.argmax(stats == 16/3)
            else:
                self.main = np.argmax(stats)

            self.substats = np.nonzero(stats)[0].tolist()
            self.substats.remove(self.main)
            self.stats = stats
            return

        self.main: int = STAT_2_NUM[main]
        self.substats: list = [STAT_2_NUM[substat] for substat in substats.keys()]
        self.stats = np.zeros(19, dtype=FLOAT_DTYPE)

        if self.main < 3:
            self.stats[self.main] = 16/3
        else:
            self.stats[self.main] = 8

        for substat, value in substats.items():
            self.stats[STAT_2_NUM[substat]] = value



    @staticmethod
    def serialize(json_dict):
        """Convert artifact dictionary into artifact object.

        Args:
            json_dict (dict): Dictionary generated by json containing
            artifact info.

        Returns:
            FastArtifact: _description_
        """
        set: str = json_dict['setKey']
        lvl: int = json_dict['level']
        slot: str = json_dict['slotKey']
        main: str = json_dict['mainStatKey']
        substats = {}
        for substat in json_dict['substats']:
            stat = substat['key']
            value = substat['value']
            coef = round(value / SUB_VALUES[stat], 1)
            substats[substat['key']] = coef
        lock = json_dict['lock']

        return FastArtifact(set, lvl, slot, main, substats, lock=lock)

    # TODO: round substat floats when printing, maybe by modifying or
    # just the displayed value
    def __str__(self):
        output = f'set: {self.set}\nlvl: {self.lvl}\nslot: {self.slot}\nmain: {STATS[self.main]}\nsub: {{'
        for idx, substat_idx in enumerate(self.substats):
            if idx != 0:
                output += ', '
            output += f'\'{str(STATS[substat_idx])}\': {self.stats[substat_idx]}'
        output += '}'
        return output
    
    def __repr__(self):
        output = f'set: {self.set}\nlvl: {self.lvl}\nslot: {self.slot}\nmain: {STATS[self.main]}\nsub: {{'
        for idx, substat_idx in enumerate(self.substats):
            if idx != 0:
                output += ', '
            output += f'\'{str(STATS[substat_idx])}\': {self.stats[substat_idx]}'
        output += '}'
        return output
    
    def __hash__(self):
        #return hash((self.lvl, self.slot, self.main, tuple(self.substats)))
        return hash((self.lvl, self.slot, self.stats.tobytes()))
    
    def __eq__(self, other):
        # TODO: add checking to normal artifacts
        return (
            self.lvl == other.lvl and
            self.slot == other.slot and
            self.main == other.main and
            np.array_equal(self.substats, other.substats)
        )
    
    def __ne__(self, other):
        return not (self == other)

    @staticmethod
    def generate(set, lvl=0, slot=None, main=None, source='domain', rng=None, seed=None):
        """Randomly generate a single artifact.

        Args:
            lvl (int, optional): Generated artifact's level. Defaults to 0.
            slot (_type_, optional): Generated artifact's slot. If None,
            randomly assign a slot. Defaults to None.
            source (str, optional): The source of the artifact, which
            affects the probability of getting 4 substats at level 0.
            Defaults to 'domain'.

        Raises:
            ValueError: If source is invalid.
            ValueError: If main stat is invalid.

        Returns:
            FastArtifact: Randomly generated artifact
        """
        if rng is None:
            rng = np.random.default_rng(seed)

        match source:
            case 'domain':
                prob = 0.2
            case 'normal boss':
                prob = 1/3
            case 'weekly boss':
                prob = 1/3
            case 'strongbox':
                prob = 1/3
            case 'domain reliquary':
                prob = 1/3
            case _:
                raise ValueError('Invalid artifact source.')
            
        num_substats = 4 if rng.random() < prob else 3
        
        if slot is None:
            slot = rng.choice(('flower', 'plume', 'sands', 'goblet', 'circlet'))
            
        if main is None:
            main_options = MAIN_PROBS[slot]
            main_stat = rng.choice(list(main_options.keys()), p=list(main_options.values()))
        else:
            if main not in MAIN_PROBS[slot].keys():
                raise ValueError(f'Invalid main stat: {main}')
            main_stat = main

        stats = np.zeros(19, dtype=FLOAT_DTYPE)
        main_idx = STAT_2_NUM[main_stat]
        if main_idx < 3:
            stats[main_idx] = 16/3
        else:
            stats[main_idx] = 8

        copy_SUB_PROBS = np.array(SUB_PROBS)
        copy_SUB_PROBS[main_idx] = 0
        probs = copy_SUB_PROBS / np.sum(copy_SUB_PROBS)

        sub_stats = rng.choice(19, size=num_substats, replace=False, p=probs)
        #sub_stats = np.random.choice(19, size=num_substats, replace=False, p=probs)
        
        for sub in sub_stats:
            stats[sub] = rng.choice((0.7, 0.8, 0.9, 1.0))

        artifact = FastArtifact(set, 0, slot, main_stat, stats=stats)
        artifact.upgrade_till(lvl, rng, seed)

        return artifact

    def random_upgrade(self, rng=None, seed=None):
        """Randomly upgrade artifact in place a single time.

        Raises:
            ValueError: If artifact is already max level.
        """
        if self.lvl == 20:
            raise ValueError('Cannot upgrade level 20 artifact')
        
        if rng is None:
            rng = np.random.default_rng(seed)

        if len(self.substats) == 3:
            probs = np.array(SUB_PROBS, dtype=FLOAT_DTYPE)
            # probs = np.array(list(SUB_PROBS_DICT.values()), dtype=FLOAT_DTYPE)
            if self.main < 10:
                probs[self.main] = 0
            for sub in self.substats:
                probs[sub] = 0
            probs /= np.sum(probs)

            new_sub = rng.choice(STATS, p=probs)
            # new_sub = rng.choice(list(SUB_PROBS_DICT.keys()), p=probs) # TODO: this doesn't need to use SUB_PROBS_DICT only SUB_PROB since it immediately converts the substat back to idx
            #new_sub = random.choices(list(copy_SUB_PROBS_DICT.keys()), weights=probs)[0]
            self.substats.append(STAT_2_NUM[new_sub])
            self.stats[STAT_2_NUM[new_sub]] = rng.choice((0.7, 0.8, 0.9, 1.0))

        else:
            temp = rng.integers(16)
            upgrade_idx = temp // 4
            upgrade_coef = [0.7, 0.8, 0.9, 1][temp % 4]

            self.stats[self.substats[upgrade_idx]] += upgrade_coef

        self.lvl = (self.lvl // 4) * 4 + 4

    def upgrade_till(self, lvl, rng=None, seed=None):
        while self.lvl // 4 < lvl // 4:
            self.random_upgrade(rng, seed)

        self.lvl = lvl

    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    @lru_cache_with_numpy(maxsize=CACHE_SIZE)
    def upgrade_distro(num_upgrades, stats):
        """Calculate the artifact's possible upgrades and their
        probability distribution.

        Args:
            lvl (int): Target level after upgrading

        Returns:
            list: List of tuples of (possibility, probability) after
            upgrading.
        """

        mask = stats == 16/3
        if np.any(mask):
            main = np.argmax(stats == 16/3)
        else:
            main = np.argmax(stats)

        substats = np.nonzero(stats)[0].tolist()
        substats.remove(main)

        # Check if currently only 3 substats
        add_substat = False
        if len(substats) == 3:
            num_upgrades -= 1
            permutations = list(generate_permutations(num_upgrades, 4))
            add_substat = True

            # Create list of possible extra substat
            new_probs = np.array(SUB_PROBS, dtype=FLOAT_DTYPE)
            new_probs[main] = 0
            for substat_idx in substats:
                new_probs[substat_idx] = 0
            new_probs /= np.sum(new_probs)
            
            num_new = np.count_nonzero(new_probs)
            num_possibilities = len(permutations) * num_new
        else:
            permutations = list(generate_permutations(num_upgrades, 4))
            num_possibilities = len(permutations)
        
        possibilities = np.tile(stats, (1 + num_possibilities, 1))
        probs = np.zeros(1 + num_possibilities)

        # Base probability for each sequence
        base_prob = (1 / 4) ** num_upgrades

        counter = 1

        for idx, counts in enumerate(permutations): # For each permutation
            prob = calculate_probability(counts, base_prob)
            for i, substat_idx in enumerate(substats): # Fill in its columns
                if add_substat:
                    possibilities[counter:counter+num_new, substat_idx] += counts[i] * 0.85
                    #probs[counter:counter+len(copy_SUB_PROBS_DICT)] = prob * np.array(copy_SUB_PROBS_DICT.values())
                else:
                    possibilities[counter, substat_idx] += 0.85 * counts[i]
                    probs[counter] = prob
                    
            if add_substat:
                for sub_idx, sub_prob in enumerate(new_probs):
                    if sub_prob == 0:
                        continue
                    possibilities[counter, sub_idx] += 0.85 * (counts[3] + 1)
                    probs[counter] = prob * sub_prob
                    counter += 1
            else:
                counter += 1

        return possibilities, probs
    
    @staticmethod
    def sample_distro(distro: list):
        possibilities = distro[0]
        probs = distro[1]
        row = np.random.choice(possibilities.shape[0], p=probs)
        return possibilities[row, :]
    
    @staticmethod
    def vectorize_targets(targets: dict):
        output = np.zeros(19, dtype=FLOAT_DTYPE)
        for target, value in targets.items():
            if target == 'crit_':
                output[8] = value
                output[9] = value
                continue

            output[STAT_2_NUM[target]] = value

        return output
    
    @staticmethod
    def unvectorize_targets(targets):
        out_list = []
        nonzero = np.nonzero(targets)[0]
        for idx in nonzero:
            out_list.append((idx, targets[idx]))
        
        return tuple(out_list)

    # TODO: maybe store scores for each (artifact, targets) pair to avoid
    # repeat calculations
    def score(self, targets: np.ndarray):
        """Calculate the current score.

        Args:
            targets (dict): Dictionary mapping a stat to a weight to
            base the score.

        Returns:
            float: Score
        """

        return self.stats @ targets

    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    @lru_cache_nested_numpy(maxsize=CACHE_SIZE)
    def score_mean(distro: list, targets: dict):
        """Calculate the average score if randomly upgrading an
        artifact.

        Args:
            distro (list): List of tuples of (possibility, probability)
            after upgrading. Generated by upgrade_distro.
            targets (dict): Dictionary mapping a stat to a weight to
            base the score. 

        Raises:
            ValueError: Distribution doesn't add to 1.

        Returns:
            float: Average score
        """
        possibilities, probs = distro
        return (possibilities @ targets) @ probs
    
    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    @lru_cache_nested_numpy(maxsize=CACHE_SIZE)
    def score_second_moment(distro: list, targets: dict):
        """Calculate the second moment of an artifact distribution.

        Args:
            distro (list): List of tuples of (possibility, probability)
            after upgrading. Generated by upgrade_distro.
            targets (dict): Dictionary mapping a stat to a weight to
            base the score. 

        Raises:
            ValueError: Distribution does not add to 1.

        Returns:
            float: Second moment of score
        """
        possibilities, probs = distro
        return np.square(possibilities @ targets) @ probs

    # TODO: maybe fix this code duplication, but it would make it 2x
    # slower without caching
    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    #@lru_cache_with_numpy(maxsize=CACHE_SIZE)
    def score_std_dev(distro: list, targets: dict):
        """Calculate the standard deviation of scores of an artifact
        distribution.

        Args:
            distro (list): List of tuples of (possibility, probability)
            after upgrading. Generated by upgrade_distro.
            targets (dict): Dictionary mapping a stat to a weight to
            base the score. 

        Raises:
            ValueError: Distribution does not add to 1.

        Returns:
            float: Standard deviation of score
        """
        return math.sqrt(FastArtifact.score_second_moment(distro, targets) - (FastArtifact.score_mean(distro, targets) ** 2))

    '''
    # TODO: test this, no idea if it actually works
    @staticmethod
    @lru_cache_nested_numpy(maxsize=CACHE_SIZE)
    def std_dev_diff(distro: list, targets: dict):
        """Calculate the decrease in standard deviation of scores if
        upgrading the source artifact for a distribution.

        Args:
            distro (list): List of tuples of (possibility, probability)
            after upgrading. Generated by upgrade_distro.
            targets (dict): Dictionary mapping a stat to a weight to
            base the score. 

        Returns:
            float: Difference in standard deviation of score
        """
        possibilities, probs = distro

        if len(distro) == 1: # TODO: make sure this works or is needed
            raise ValueError('Maxed artifacts cannot be upgraded.')

        current_std_dev = FastArtifact.score_std_dev(distro, targets)

        single_possibilities, single_probs = FastArtifact.upgrade_distro(1, possibilities[0, :])
        new_std_dev = 0
        for artifact in single_possibilities:
            new_std_dev += FastArtifact.score_std_dev()
        
        for artifact, prob in single_distro:
            sub_distro = FastArtifact.upgrade_distro(artifact, 20)
            sub_std_dev = FastArtifact.score_std_dev(sub_distro, targets)
            new_std_dev += sub_std_dev * prob
        
        return current_std_dev - new_std_dev
    '''

    # TODO: consolidate distro files of same slot into one file. Make
    # first value in each row the main stat to differentiate. This is
    # expensive, so also store the score distro in disk.
    # This is because artifacts of other main stats still compete. An
    # ATK goblet may be better than a DMG bonus. Can't greedily compute
    # them separately. 

    @classmethod
    def class_top_x_per(cls, scores, slot, targets):
        unvect_targets = FastArtifact.unvectorize_targets(targets)
        # key = slot + '_' + main

        if unvect_targets not in FastArtifact.score_cdfs:
            FastArtifact.score_cdfs[unvect_targets] = {}
            print('Scores not loaded')

        if slot not in FastArtifact.score_cdfs[unvect_targets]:
            filename = 'distros/scores/'
            for idx, coef in unvect_targets:
                filename += str(idx) + '_' + str(coef) + '_'

            filename = filename[:-1]
            Path(filename).mkdir(parents=True, exist_ok=True)
            filename += '/' + slot + '.npy'
            try: # TODO: maybe check for the file to prevent nesting
                FastArtifact.score_cdfs[unvect_targets][slot] = np.load(filename)
                print('Scores loaded from file.')
            except:
                print('Scores not found. Generating...')
                print(filename)
                upgrades = np.load('distros/upgrades.npy') # Maybe don't repeat this
                probs = np.load('distros/upgrade_probs.npy')
                bases = np.load(f'distros/{slot}.npy')
                
                distro = {}
                for idx, base in enumerate(bases):
                    for upgrade, prob in zip(upgrades, probs):
                        stats = np.zeros(19, dtype=float)

                        main = base[0]
                        if main < 3:
                            stats[int(main)] = 16/3
                        else:
                            stats[int(main)] = 8

                        for a, b in zip(base[1:], upgrade):
                            stats[int(a)] = b / 10

                        score = stats @ targets
                        
                        total_prob = prob * base[-1]
                        if score in distro:
                            distro[score] += total_prob
                        else:
                            distro[score] = total_prob

                cdf = np.zeros((len(distro), 2))
                cdf[:, 0] = sorted(distro.keys())
                # sorted_scores = np.array(sorted(distro.keys()))
                total_probs = np.array([distro[score] for score in cdf[:, 0]])
                cdf[:, 1] = np.cumsum(total_probs)

                FastArtifact.score_cdfs[unvect_targets][slot] = cdf
                np.save(filename, cdf)
                print('Scores generated and saved.')

        cdf = FastArtifact.score_cdfs[unvect_targets][slot]
        indices = np.searchsorted(cdf[:, 0], scores, side='left')

        return 1 - cdf[:, 1][indices]
    
    def top_x_per(self, targets):
        if self.lvl != 20:
            raise ValueError('Can only rate maxed artifacts.')
        
        score = self.score(targets)
        slot = self.slot
        return FastArtifact.class_top_x_per(score, slot, targets)
    
    @classmethod
    def avg_req_to_beat(cls, distro, targets, slot):
        possibilities, probs = distro
        scores = possibilities @ targets
        percents = FastArtifact.class_top_x_per(scores, slot, targets)
        num_req = 1 / percents
        return num_req @ probs

    @staticmethod
    def static_upgrade_req_exp(lvl):
        upgrade_lvl = 4 * ((lvl // 4) + 1)
        return ARTIFACT_REQ_EXP[upgrade_lvl] - ARTIFACT_REQ_EXP[lvl]

    def upgrade_req_exp(self):
        """Estimate how much EXP is needed to upgrade once.

        Returns:
            int: Required EXP
        """
        upgrade_lvl = 4 * ((self.lvl // 4) + 1)
        return ARTIFACT_REQ_EXP[upgrade_lvl] - ARTIFACT_REQ_EXP[self.lvl]

    @staticmethod
    def static_salvage_exp(lvl):
        return int(3780 + 0.8 * ARTIFACT_REQ_EXP[lvl])

    def salvage_exp(self):
        """Estimate how much EXP given when salvaged.

        Returns:
            int: Salvaged EXP
        """
        return int(3780 + 0.8 * ARTIFACT_REQ_EXP[self.lvl])

    @staticmethod
    def read_json(filename, split=False):
        """Read JSON of artifacts.

        Args:
            filename (str): JSON filename.
            split (bool, optional): Whether to split the list of
            artifacts into 6 separate lists based on their levels.
            Defaults to False. 

        Raises:
            ValueError: If format isn't GOOD.

        Returns:
            list: List of List of FastArtifact if split, List of FastArtifact
            otherwise.
        """
        with open(filename) as f:
            data = json.load(f) 
        
        if data['format'] != 'GOOD':
            raise ValueError('Format is not GOOD')
        
        artifacts = []
        artifact_dicts = data['artifacts']

        if split:
            buckets = [[] for _ in range(6)]
            for artifact_dict in artifact_dicts:
                if artifact_dict['rarity'] != 5:
                    continue

                (buckets[artifact_dict['level'] // 4]).append(FastArtifact.serialize(artifact_dict))

            return buckets
        else:
            for artifact_dict in artifact_dicts:
                if artifact_dict['rarity'] != 5:
                    continue

                artifacts.append(FastArtifact.serialize(artifact_dict))
        
        return artifacts
    
    @staticmethod
    def split_slot(artifacts):
        """Split a list of artifacts into 5 seperate lists based on
        their slots.

        Args:
            artifacts (list): List of FastArtifact objects.

        Raises:
            ValueError: FastArtifact is malformed and has an invalid slot.

        Returns:
            tuple: Tuple of 5 lists for each slot
        """
        flowers = []
        plumes = []
        sands = []
        goblets = []
        circlets = []
        for artifact in artifacts:
            match artifact.slot:
                case 'flower':
                    flowers.append(artifact)
                case 'plume':
                    plumes.append(artifact)
                case 'sands':
                    sands.append(artifact)
                case 'goblet':
                    goblets.append(artifact)
                case 'circlet':
                    circlets.append(artifact)
                case _:
                    raise ValueError('Invalid artifact slot')
        
        return flowers, plumes, sands, goblets, circlets
    
    @staticmethod
    def split_lvl(artifacts):
        """Split a list of artifacts into 6 seperate lists based on
        their levels.

        Args:
            artifacts (list): List of FastArtifact objects.

        Raises:
            ValueError: FastArtifact is malformed and has an invalid level.

        Returns:
            tuple: Tuple of 6 lists for each level
        """
        # TODO: This is so stupid lmao but it works, im too lazy to make
        # it smarter
        zeros = []
        fours = []
        eights = []
        twelves = []
        sixteens = []
        twenties = []
        for artifact in artifacts:
            match artifact.lvl // 4:
                case 0:
                    zeros.append(artifact)
                case 1:
                    fours.append(artifact)
                case 2:
                    eights.append(artifact)
                case 3:
                    twelves.append(artifact)
                case 4:
                    sixteens.append(artifact)
                case 5:
                    twenties.append(artifact)
                case _:
                    raise ValueError('Invalid artifact level')

        return zeros, fours, eights, twelves, sixteens, twenties