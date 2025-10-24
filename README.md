# Artifact Sort

Sort Genshin Impact artifacts by considering a suite of configurable
optimization targets, sets, and rankers. Are any of these problems
relevant to you?

- How long is it going to take to improve my current artifacts? Is it
  even worth farming for this set anymore?
- What artifact should I define with the Artifact Transmuter? If I do,
  how much resin am I saving on average?
- Is this artifact worth reshaping its substats? Which artifact is most
  resin efficient to choose?
- I need to get rid of some artifacts, but have no idea with is my
  "worst", especially considering multiple possible builds and targets
  at once.
- There might be a future character that needs [insert super niche weird
  build] and I'm too paranoid to get rid of anything.
- Genshin Optimizer tells me my current best builds, and recommends
  which artifacts to upgrade my greedily replacing single artifacts, but
  that is too fine-grained. I want something that generalizes "good"
  artifacts.
- I don't have a full/good build for Genshin Optimizer to base its
  upgrade recommendations on.

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
1. Export in-game artifacts to GOODv3 using Irminsul. Currently only
   works with Irminsul because it's the only scanner that reports
   initialValue for substats, which is used during reshaping analysis.
   Support for other OCR-based scanners is in progress.
2. Place the scan within the project directory.
3. <p>Run:<br>
   Locking guide only</p>

   ```sh
   python rank.py <input json> > output.txt
   ```

   Locking guide and resin guide
   ```sh
   python rank.py <input json> <artifact set> <optimization target> > output.txt
   ```
   The artifact set and optimization target must use GOOD formatted
   strings, for example
   ```sh
   python rank.py <input json> GoldenTroupe "{'atk_': 6, 'atk': 2, 'crit_': 8}" > output.txt
   ```
   Optimization is a dictionary with a weighted sum of the considered
   stats. The current input formatting isn't user friendly, and will be
   fixed at a later date, likely with a GUI. For more examples of
   properly formatted optimization targets, look in targets.py (Warning:
   it's a mess in there).

   You can also specify a power increase threshold of x%. If not
   specified, it defaults to ANY%, or 0%. For example, a
   5% increase would be
   ```sh
   python rank.py <input json> GoldenTroupe "{'atk_': 6, 'atk': 2, 'crit_': 8}" 0.05 > output.txt
   ```
4. Inspect results in output.txt. Results are redirected to a seperate
   file since they may be long. If the locking guide recommends
   unlocking something you aren't comfortable trashing, feel free to
   skip it. Properly weighting targets is still a WIP. There is lots of
   data not currently presented in the output. The GUI is under
   development and function interfaces will likely be reworked at some
   point.
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
- [X] Analysis for defining
- [X] Analysis for reshaping
- [ ] Automatic locking/unlocking
- [ ] Packaging to .exe