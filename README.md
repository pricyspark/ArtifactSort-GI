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
   cd ArtifactSort
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

   mamba
   ```sh
   mamba env create -f environment.yml
   mamba activate artifact_sort
   ```

   conda
   ```sh
   conda env create -f environment.yml
   conda activate artifact_sort
   ```
3. Compile GUI elements
   ```sh
   pyside6-uic mainwindow.ui -o MainWindow.py
   pyside6-rcc resources.qrc -o resources.py
   ```
## Usage
Disclaimer: This project is in active development. There are guaranteed
to be bugs and unaccounted for edge cases. Improper usage will likely
crash the program or cause en error. This is fine, simply close the
window and relaunch.
1. Export in-game artifacts using a scanner.
   
   For best results, scan with Irminsul and Inventory Kamera. Irminsul
   captures extra data to ensure maximum accuracy. Inventory Kamera
   keeps track of scan order, so artifacts can be presented in the same
   order as they are in game. Otherwise finding specific artifacts becomes
   a big hassle. This is a surprisingly rare trait, for example Irminsul
   and AdeptiScanner don't maintain order. Mileage may vary for others.

   Note: Even in-game, Genshin doesn't seem to have a concrete ordering,
   and there can be variations in the order even when the inventory
   doesn't change. To guarantee order correctness, analyze immediately after
   scanning. Sorting by order obtained gives consistent ordering every
   time, but Inventory Kamera automatically disables this.
2. <p>Run:<br>

   ```sh
   python gui.py
   ```
3. In the opened window, select your scan(s). If you only have one scan
   (Irminsul), select it as the main scan. If you have two scans, select
   the ordered scan as the main scan, and the second one as the
   additional scan. Click "calculate".

4. Wait for the analysis to finish. The first time you run this, will
   take several minutes. Subsequent calculations will be faster. There
   is a progress bar in rendered on the command line. The GUI window
   will freeze during this time, and is normal.

5. Check results in other tabs.

   The ***upgrade tab*** recommends ~20 artifacts most likely to
   become your best  for some target. (Targets for corresponding sets
   are listed in targets.py). This is likely not very useful however, as
   recommendations don't favor traditional optimization targets, so
   "weird" artifacts will get mixed in.

   The ***lock tab*** gives recommendations on what you should lock and
   unlock. Its locking strategy is "lock everything except your worst
   100 artifacts." Any artifacts that don't follow this scheme are
   listed. It is recommended to use the auto-locking feature in-game to
   lock ALL 5* artifacts by default, and use the lock tab to unlock
   accordingly. This is very conservative and ensures you only trash
   your absolute worst artifacts.

   The ***define and reshape tab*** provides insight for resin efficiency.
   Select a set and optimization target, and it will return expected
   resin requirements to farm improvements of at least 0%, 1%, and 5%.
   It also returns how much resin you save on average if you instead
   define or reshape an artifact. Optimization targets are defined by a
   dictionary with a weighted sum of the considered stats. The current
   input formatting isn't user friendly, and a better input method is in
   progress. For more examples of properly formatted optimization
   targets, look in targets.py. (Warning: it's a mess in there)

   Example optimization target:
   ```
   {'atk_': 6, 'atk': 2, 'crit_': 8}
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
- [X] GUI
- [X] Analysis for defining
- [X] Analysis for reshaping
- [X] Saving cache to disk
- [ ] Automatic locking/unlocking
- [ ] Packaging to .exe
- [ ] Smarter caching
- [ ] Multiprocess/multithread (curse you GIL)
- [ ] Improve GUI, add more customization and info