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

NUM_2_STAT = ['hp', 'atk', 'def', 'hp_', 'atk_', 'def_', 'enerRech_', 'eleMas', 
              'critRate_', 'critDMG_', 'pyro_dmg_', 'electro_dmg_', 'cryo_dmg_', 
              'hydro_dmg_', 'dendro_dmg_', 'anemo_dmg_', 'geo_dmg_', 
              'physical_dmg_', 'heal_']
STAT_2_NUM = {stat: index for index, stat in enumerate(NUM_2_STAT)}

CACHE_SIZE = 2000
MAIN_PROBS = {
    'flower' : {'hp': 1},
    'plume'  : {'atk': 1},
    'sands'  : {'hp_': 8,
                'atk_': 8,
                'def_': 8,
                'enerRech_': 3,
                'eleMas': 3},
    'goblet' : {'hp_': 77,
                'atk_': 77,
                'def_': 76,
                'pyro_dmg_': 20, 
                'electro_dmg_': 20,
                'cryo_dmg_': 20,
                'hydro_dmg_': 20,
                'dendro_dmg_': 20,
                'anemo_dmg_': 20,
                'geo_dmg_': 20,
                'physical_dmg_': 20,
                'eleMas': 10},
    'circlet': {'hp_': 11,
                'atk_': 11,
                'def_': 11,
                'critRate_': 5,
                'critDMG_': 5,
                'heal_': 5,
                'eleMas': 2}
}

SUB_PROBS = {
    'hp': 6,
    'atk': 6,
    'def': 6,
    'hp_': 4,
    'atk_': 4,
    'def_': 4,
    'enerRech_': 4,
    'eleMas': 4,
    'critRate_': 3,
    'critDMG_': 3
}

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
    def __init__(self, set, lvl, slot, main, substats, lock=False):

        self.set: str = set
        self.lvl: int = lvl
        self.slot: str = slot

        #if array is not None:
        #    self.main = np.argmax(array)

        self.main: int = STAT_2_NUM[main]
        self.substats: list = [STAT_2_NUM[substat] for substat in substats.keys()]
        self.stats = np.zeros(19, dtype=FLOAT_DTYPE)

        if self.main < 3:
            self.stats[self.main] = 16/3
        else:
            self.stats[self.main] = 8

        for substat, value in substats.items():
            self.stats[STAT_2_NUM[substat]] = value

        self.lock = lock
        self.last_score = None


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
        output = f'set: {self.set}\nlvl: {self.lvl}\nslot: {self.slot}\nmain: {NUM_2_STAT[self.main]}\nsub: {{'
        for idx, substat_idx in enumerate(self.substats):
            if idx != 0:
                output += ', '
            output += f'\'{str(NUM_2_STAT[substat_idx])}\': {self.stats[substat_idx]}'
        output += '}'
        return output
    
    def __repr__(self):
        output = f'set: {self.set}\nlvl: {self.lvl}\nslot: {self.slot}\nmain: {NUM_2_STAT[self.main]}\nsub: {{'
        for idx, substat_idx in enumerate(self.substats):
            if idx != 0:
                output += ', '
            output += f'\'{str(NUM_2_STAT[substat_idx])}\': {self.stats[substat_idx]}'
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
    def generate(set, lvl=0, slot=None, main=None, source='domain'):
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
            
        num_substats = 4 if random.random() < prob else 3
        
        if slot is None:
            slot = random.choice(['flower', 'plume', 'sands', 'goblet', 'circlet'])
            
        if main is None:
            main_options = MAIN_PROBS[slot]
            main_stat = random.choices(list(main_options.keys()), weights=main_options.values())[0]
        else:
            if main not in MAIN_PROBS[slot].keys():
                raise ValueError('Invalid main stat.')
            main_stat = main

        copy_SUB_PROBS = SUB_PROBS.copy()
        copy_SUB_PROBS.pop(main_stat, KeyError)
        prob = np.array(list(copy_SUB_PROBS.values()), dtype=FLOAT_DTYPE)
        prob /= np.sum(prob)
        sub_stats = np.random.choice(list(copy_SUB_PROBS.keys()), size=num_substats, replace=False, p=prob)

        substats = {}
        for sub in sub_stats:
            substats[str(sub)] = random.choice((0.7, 0.8, 0.9, 1.0))

        artifact = FastArtifact(set, 0, slot, main_stat, substats)
        num_upgrades = lvl // 4 # TODO: find a better way to do this
        for _ in range(num_upgrades):
            artifact.random_upgrade()

        return artifact

    def random_upgrade(self):
        """Randomly upgrade artifact in place a single time.

        Raises:
            ValueError: If artifact is already max level.
        """
        if self.lvl == 20:
            raise ValueError('Cannot upgrade level 20 artifact')
        
        self.last_score = None

        if len(self.substats) == 3:
            copy_SUB_PROBS = SUB_PROBS.copy()
            copy_SUB_PROBS.pop(self.main, KeyError)
            for substat in self.substats:
                copy_SUB_PROBS.pop(NUM_2_STAT[substat], KeyError)

            probs = np.array(list(copy_SUB_PROBS.values()), dtype=FLOAT_DTYPE)
            probs /= np.sum(probs)

            new_sub = random.choices(list(copy_SUB_PROBS.keys()), weights=probs)[0]
            self.substats.append(STAT_2_NUM[new_sub])
            self.stats[STAT_2_NUM[new_sub]] = random.choice((0.7, 0.8, 0.9, 1.0))

        else:
            temp = random.randint(0, 15)
            upgrade_idx = temp // 4
            upgrade_coef = [0.7, 0.8, 0.9, 1][temp % 4]

            self.stats[self.substats[upgrade_idx]] += upgrade_coef

        self.lvl = (self.lvl // 4) * 4 + 4

    @functools.lru_cache(maxsize=CACHE_SIZE)
    def upgrade_distro(self, lvl):
        """Calculate the artifact's possible upgrades and their
        probability distribution.

        Args:
            lvl (int): Target level after upgrading

        Returns:
            list: List of tuples of (possibility, probability) after
            upgrading.
        """
        # Calculate the number of upgrades needed
        num_upgrades = (lvl // 4) - (self.lvl // 4)

        # Check if currently only 3 substats
        add_substat = False
        if len(self.substats) == 3:
            num_upgrades -= 1
            add_substat = True
            self.substats.append(-1)
            new_coefs = []

        # Base probability for each sequence
        base_prob = (1 / 4) ** num_upgrades

        # Generate permutations and calculate probabilities
        # TODO: verify all the copies are necessary
        #possibilities = {self: 0}
        possibilities = [(self, 0)]
        total_prob = 0
        for counts in generate_permutations(num_upgrades, 4):
            prob = calculate_probability(counts, base_prob)
            temp = copy.deepcopy(self)
            temp.lvl = lvl
            temp.last_score = None
            for idx, substat_idx in enumerate(temp.substats):
                if substat_idx == -1:
                    new_coefs.append(0.85 * (1 + counts[idx])) # TODO: add random upgrade coefs
                else:
                    temp.stats[substat_idx] += counts[idx] * 0.85 # TODO: add random upgrade coefs
            
            possibilities.append((temp, prob))
            #possibilities[temp] = prob
            total_prob += prob
        #print(self)
        #print()
        #print(possibilities)
        if add_substat:
            # Pop the first artifact, which is a copy of the original
            # artifact
            possibilities.pop(0)

            # Create list of possible extra substat
            copy_SUB_PROBS = SUB_PROBS.copy()
            copy_SUB_PROBS.pop(NUM_2_STAT[self.main], KeyError)
            for substat_idx in self.substats:
                copy_SUB_PROBS.pop(NUM_2_STAT[substat_idx], KeyError)
            total = sum(copy_SUB_PROBS.values())
            for substat in copy_SUB_PROBS:
                copy_SUB_PROBS[substat] /= total

            # Create a backup of the original possibiilities to base new
            # copies off of
            original_possibilities = possibilities.copy()

            # Add back original artifact
            possibilities = [(self, 0)]

            # For each possible new substat
            for sub, sub_prob in copy_SUB_PROBS.items():
                # For each possible artifact
                for idx, (original_artifact, artifact_prob) in enumerate(original_possibilities):
                    # Create a new copy and replace the placeholder None
                    # substat with the real one. Multiply by the substat
                    # probability coefficient and append to the final
                    # list of possibilities
                    artifact = copy.deepcopy(original_artifact)
                    artifact.substats.append(STAT_2_NUM[sub])
                    artifact.stats[STAT_2_NUM[sub]] = new_coefs[idx]
                    artifact.substats.remove(-1)
                    possibilities.append((artifact, sub_prob * artifact_prob))

            self.substats.remove(-1)

        return tuple(possibilities)
    
    @staticmethod
    def sample_distro(distro: list):
        possibilities = [t[0] for t in distro]
        probs = [t[1] for t in distro]
        return random.choices(possibilities, weights=probs, k=1)[0]
    
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
        if self.last_score is not None:
            return self.last_score

        score = self.stats @ targets
        self.last_score = score
        return score

    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    @lru_cache_with_numpy(maxsize=CACHE_SIZE)
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
        mean = 0

        probs = [t[1] for t in distro]

        if not math.isclose(sum(probs), 1):
            raise ValueError('Distribution does not add to 1.')

        for artifact, prob in distro:
            mean += artifact.score(targets) * prob

        return mean
    
    #@functools.lru_cache(maxsize=CACHE_SIZE)
    @staticmethod
    @lru_cache_with_numpy(maxsize=CACHE_SIZE)
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
        probs = [t[1] for t in distro]

        if not math.isclose(sum(probs), 1):
            raise ValueError('Distribution does not add to 1.')
        
        second_moment = 0
        
        for artifact, prob in distro:
            second_moment += (artifact.score(targets) ** 2) * prob

        return math.sqrt(second_moment) 

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
        probs = [t[1] for t in distro]

        if not math.isclose(sum(probs), 1):
            raise ValueError(f'Distribution does not add to 1.')
        
        mean = 0
        second_moment = 0
        
        for artifact, prob in distro:
            score = artifact.score(targets)
            mean += score * prob
            second_moment += (score ** 2) * prob

        variance = second_moment - (mean ** 2)

        return math.sqrt(variance) 

    # TODO: test this, no idea if it actually works
    @staticmethod
    @lru_cache_with_numpy(maxsize=CACHE_SIZE)
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
        if len(distro) == 1:
            raise ValueError('Maxed artifacts cannot be upgraded.')

        current_std_dev = FastArtifact.score_std_dev(distro, targets)

        for artifact, prob in distro:
            if prob == 0:
                current_artifact = artifact
                break

        new_std_dev = 0
        single_distro = FastArtifact.upgrade_distro(current_artifact, 4 * ((current_artifact.lvl // 4) + 1))
        for artifact, prob in single_distro:
            sub_distro = FastArtifact.upgrade_distro(artifact, 20)
            sub_std_dev = FastArtifact.score_std_dev(sub_distro, targets)
            new_std_dev += sub_std_dev * prob
        
        return current_std_dev - new_std_dev

    def upgrade_req_exp(self):
        """Estimate how much EXP is needed to upgrade once.

        Returns:
            int: Required EXP
        """
        upgrade_lvl = 4 * ((self.lvl // 4) + 1)
        return ARTIFACT_REQ_EXP[upgrade_lvl] - ARTIFACT_REQ_EXP[self.lvl]

    def salvage_exp(self):
        """Estimate how much EXP given when salvaged.

        Returns:
            int: Salvaged EXP
        """
        return int(3780 + 0.8 * ARTIFACT_REQ_EXP[self.lvl])

    @staticmethod
    def sort_potential(artifacts, targets_list, special_targets_list=None, 
                       set_targets_list=None): # TODO: maybe think of better name
        distros = []
        for artifact in artifacts:
            distros.append((artifact.upgrade_distro(20), artifact.set))

        num_special_targets = 0 if special_targets_list is None else len(special_targets_list)
        num_set_targets = 0 if set_targets_list is None else len(set_targets_list)
        
        means = np.zeros((len(artifacts), len(targets_list) + num_special_targets + num_set_targets))
        sorted_idxs = np.zeros_like(means, dtype=int)

        for idx, (targets, num) in enumerate(targets_list):
            target_means = [FastArtifact.score_mean(distro, targets) for distro, _ in distros]

            sorted_means = sorted(target_means, reverse=True)
            sorted_idx = np.array([sorted_means.index(mean) for mean in target_means], dtype=int)
            sorted_idx[sorted_idx >= num] = np.iinfo(sorted_idx.dtype).max
            sorted_idxs[:, idx] = sorted_idx
            means[:, idx] = target_means

        if special_targets_list is not None:
            for idx, (targets, num) in enumerate(special_targets_list):
                idx += len(targets_list)
                target_means = [FastArtifact.score_mean(distro, targets) for distro, _ in distros]

                sorted_means = sorted(target_means, reverse=True)
                sorted_idx = np.array([sorted_means.index(mean) for mean in target_means], dtype=int)
                sorted_idx[sorted_idx >= num] = np.iinfo(sorted_idx.dtype).max
                sorted_idxs[:, idx] = sorted_idx
                means[:, idx] = target_means
        
        if set_targets_list is not None:
            for idx, (set, targets, num) in enumerate(set_targets_list):
                idx += len(targets_list) + num_special_targets
                target_means = []
                for distro, distro_set in distros:
                    if set == distro_set:
                        target_means.append(FastArtifact.score_mean(distro, targets))
                    else:
                        target_means.append(-1)

                sorted_means = sorted(target_means, reverse=True)
                sorted_idx = np.array([sorted_means.index(mean) for mean in target_means], dtype=int)
                #sorted_idx[sorted_idx >= num] = np.iinfo(sorted_idx.dtype).max
                sorted_idx[sorted_idx >= num] = np.iinfo(sorted_idx.dtype).max
                try:
                    if sorted_means.index(-1) < num:
                        sorted_idx[sorted_idx >= sorted_means.index(-1)] = np.iinfo(sorted_idx.dtype).max
                except:
                    pass
                sorted_idxs[:, idx] = sorted_idx
                means[:, idx] = target_means

        np.save('asdf.npy', sorted_idxs)
        min_idx = list(np.min(sorted_idxs, axis=1))

        #output = dict(zip(artifacts, zip(min_idx, means)))
        #return dict(sorted(output.items(), key=lambda item: item[1][0], reverse=True))
        output = dict(zip(artifacts, min_idx))
        return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))

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
    
targets = {'atk_': 1, 'atk': 1/3, 'crit_': 4/3}
targets_vector = FastArtifact.vectorize_targets(targets)

asdf = FastArtifact('set', 0, 'flower', 'hp', {'atk': 0.8, 'def': 0.7, 'atk_': 0.9})
asdf.upgrade_distro(20)