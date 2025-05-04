import numpy as np
import artifact as Artifact

def create_dataset(slot, lvls, targets, source='domain', num_trials=1000):
    artifacts = Artifact.generate(slot, lvls, source)
    for i in range(num_trials):
        original_artifacts = artifacts.copy()
        artifact
        artifacts = original_artifacts
    num = 10000
    totals = np.zeros(num)
    avg = np.zeros(num)
    targets = Artifact.vectorize({'atk_': 3, 'atk': 1, 'crit_': 4})
    for i in range(num):
        artifacts = Artifact.generate('flower', size=200, seed=i)
        totals[i] = (Artifact.simulate_exp(artifacts, np.zeros(200, dtype=int), targets, Artifact.upper_bound))

    cumsum = np.cumsum(totals)
    for i in range(len(cumsum)):
        avg[i] = cumsum[i] / (i + 1)