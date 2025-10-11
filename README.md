# Artifact Sort

Sort Genshin Impact artifacts by considering a suite of configurable
optimization targets, sets, and rankers. Are any of these problems
relevant to you?

- I need to get rid of some artifacts, but have no idea with is my
  "worst", especially considering multiple possible builds and targets
  at once.
- There might be a future character that needs [insert super niche weird
  build] and I'm too paranoid to get rid of anything.
- Genshin Optimizer tells me my current best builds, and recommends
  which artifacts to upgrade my greedily replacing single artifacts, but
  that is too fine-grained. I want something that generalizes "good"
  artifacts.
- I don't have a full/good build for Genshin Optimizer to accurately
  recommend good artifacts to upgrade.

If so, then Artifact Sort can help you!

## Installation
1. Clone the repo
   ```sh
   git clone https://github.com/pricyspark/ArtifactSort.git
   ```
2. <p>Set up environment using:<br>
   venv + pip (Windows)</p>

   ```sh
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   venv + pip (macOS/Linus)
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   conda
   ```sh
   conda env create -f environment.yml
   conda activate artifact_sort
   ```
## Usage
1. Export in-game artifacts to GOODv3 with your preferred scanner
   (AdeptiScanner, Irminsul, Artiscan, Inventory Kamera, etc.).
2. Place the scan within the project directory.
3. Run
   ```sh
   python rank.py ARTIFACTS_GOODv3.json
   ```
## Cleanup
venv + pip
```sh
deactivate
rm -rf .venv
```
conda
```sh
conda deactivate
conda env remove -n artifact_sort
```
## Roadmap
- [ ] GUI
- [ ] Analysis for defining
- [ ] Analysis for reshaping
- [ ] Automatic locking/unlocking