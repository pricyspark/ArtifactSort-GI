```python
from fast import FastArtifact

# Load artifacts
artifacts = FastArtifact.read_json('example.json')
flowers, plumes, sands, goblets, circlets = FastArtifact.split_slot(artifacts)
maxed, nonmaxed = FastArtifact.split_maxed(flowers)

# Define targets and optimization parameters
targets = FastArtifact.vectorize_targets({'atk_': 3, 'atk': 1, 'crit_': 4})
funs = FastArtifact.generate_funs('functions/flower.json')

# Classify artifacts to keep
ratings = FastArtifact.rate(nonmaxed, funs)
print('Keep:')
for artifact, keep in zip(nonmaxed, ratings):
    if keep:
        print(artifact)
        print()

print('Don\'t keep:')
for artifact, keep in zip(nonmzed, ratings):
    if not keep:
        print(artifact)
        print()
```