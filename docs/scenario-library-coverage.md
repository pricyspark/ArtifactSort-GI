# Scenario library coverage and research release

Codex assisted with the research, numerical authoring, coverage inventory and
encoding checks. Content revision: `roster-research-2026-10-05-1`; research date:
2026-10-05. **Coverage is partial and every numerical definition is draft.**

The batch provides 42 established event definitions, 31 parameter sensitivities,
and five structural prospects, covering 14 characters and 15 character/role
families. There are zero game-validated scenarios. The coverage register inventories
120 character records and 63 artifact sets from the pinned source, all seven
Traveler elements, and two additional KQM guide-index entries. Seventeen sets
cannot supply five-star artifacts. No GO account inventory or saved build winner
was used to choose coverage.

## Deliverables and offline reproduction

- [Numerical v4 library](../scenarios/library.json)
- [Research sidecar](../scenarios/library.research.json)
- [Executable draft mechanics manifest](../scenarios/library.mechanics.json)
- [Machine-readable character/role/set coverage](../scenarios/library.coverage.json)
- [Actual validation observations and file digests](../scenarios/library.validation.json)
- [Pinned numerical source snapshot](../scenarios/research/source-snapshot.json),
  [coverage plan](../scenarios/research/coverage-plan.json), and
  [scalar reference cases](../scenarios/research/reference-cases.json)

Rebuild and check without internet access:

```sh
python scripts/build_scenario_library.py
python scripts/validate_scenario_library.py --write-results
python -m pytest -q tests/test_researched_library.py tests/test_library.py
```

The builder separates numerical formulas/effects, scenario assumptions, and
coverage reporting into cohesive authoring modules. It overwrites only this
batch's generated files; the example and pilot are preserved. Increment the
content revision when publishing changed definitions, and use a new mechanics
ID if changing the release's rules. `--write-results` attaches performed encoding
checks to the sidecar and regenerates the validation report. It never promotes
research status. The runtime requires `allow_draft=True` for this batch.

The mechanics ID is `research-subset-go-d517a2562e77-v1`. Its numerical source is
[GO commit d517a2562e770f056960ffeac8bc686fd3452892](https://github.com/frzyc/genshin-optimizer/tree/d517a2562e770f056960ffeac8bc686fd3452892).
The snapshot records source file SHA256 hashes and each level-90 derivation:
level-one stat times the level-90 growth factor, plus the A6 addition. Character
and weapon ATK are combined only in base ATK; weapon secondary stats and character
ascension ratios remain additions. The generated GO table already uses ratios;
normalization is determined by field contracts, never number size.

The manifest declares recognized GOOD keys and the library supplies executable
effects. Recognition is not full mechanics support. The source snapshot does not
declare a game patch; `7.1` in the manifest is the research context visible in the
[KQM guide index](https://keqingmains.com/), not a claim that every source guide
has been updated to that patch. Vesna and Vodyanitsa have index entries but no
matching stats in this GO snapshot. Their GOOD keys, availability, and kits need
research. All source-roster release flags remain individually unaudited.

## Research-backed numerical subset

Each family is one character and role. Set and weapon/condition alternatives
share that family, while Shinobu's healing and Hyperbloom uses remain separate.
These are event objectives, not complete rotations or an exhaustive kit model.

| Character | Numerical family | Established definitions | Event modeled |
| --- | --- | ---: | --- |
| [Albedo](https://keqingmains.com/q/albedo-quickguide/) | `Albedo/off-field-damage` | 6 | Transient Blossom, ordinary and documented Hexerei addition |
| [Barbara](https://keqingmains.com/q/barbara-quickguide/) | `Barbara/healing` | 2 | Periodic Skill received healing |
| [Fischl](https://keqingmains.com/q/fischl-quickguide/) | `Fischl/off-field-damage` | 2 | Non-Quicken Oz projectile |
| [Jean](https://keqingmains.com/q/jean-quickguide/) | `Jean/sunfire-trigger` | 1 | Owned Sunfire Pyro Swirl |
| [KamisatoAyaka](https://keqingmains.com/q/ayaka-quickguide/) | `KamisatoAyaka/quickswap-damage` | 4 | Cutting Burst tick, Cryo/Frozen/Hunter snapshots |
| [KukiShinobu](https://keqingmains.com/q/shinobu-quickguide/) | `KukiShinobu/healing` | 2 | Owned Hyperbloom core or ring received healing |
| [KukiShinobu](https://keqingmains.com/q/shinobu-quickguide/) | `KukiShinobu/hyperbloom-trigger` | 5 | Owned Hyperbloom core or ring received healing |
| [Nahida](https://keqingmains.com/q/nahida-quickguide/) | `Nahida/off-field-damage` | 3 | Mixed ATK/EM Tri-Karma with owned Spread |
| [Neuvillette](https://keqingmains.com/q/neuvillette-quickguide/) | `Neuvillette/on-field-damage` | 2 | Enhanced charged-attack tick at explicit HP/stack state |
| [RaidenShogun](https://keqingmains.com/q/raiden-quickguide/) | `RaidenShogun/hyperbloom-trigger` | 3 | Owned Hyperbloom core |
| [Thoma](https://keqingmains.com/q/thoma-quickguide/) | `Thoma/burgeon-trigger` | 5 | Owned Burgeon core |
| [Xingqiu](https://keqingmains.com/q/xingqiu-quickguide/) | `Xingqiu/off-field-damage` | 2 | One Rain Sword |
| [Yaoyao](https://keqingmains.com/q/yaoyao-quickguide/) | `Yaoyao/healing` | 1 | One direct radish heal |
| [Yelan](https://keqingmains.com/q/yelan-quickguide/) | `Yelan/off-field-damage` | 2 | One Exquisite Throw projectile |
| [Zhongli](https://keqingmains.com/q/zhongli-quickguide/) | `Zhongli/shielding` | 2 | Geo shield effective absorption |

Meaningful alternatives include Golden Troupe/mixed Fischl, Emblem/mixed Hydro
Burst users, Husk/Golden/mixed Albedo, Blizzard/Hunter/mixed Ayaka,
Hunter/Hydro/HP combinations for Neuvillette, multiple Hyperbloom/Burgeon sets,
and healing/HP combinations. Nahida retains both ATK and EM scaling, Spread,
and her EM-derived talent damage/crit caps; EM characters are not assigned a
pure ATK proxy. See the sidecar for exact coefficients, weapon states and sources.

The effect rules encode actual candidate counts and explicit activation states:
[KQM's artifact reference](https://library.keqingmains.com/equipment/artifacts)
supports the implemented bonuses and distinguishes holder stats from team buffs.
The reaction score uses level, EM and resistance, excluding ordinary crit and
DEF, following [TCL's damage formulas](https://library.keqingmains.com/combat-mechanics/damage/damage-formula)
and the pinned GO level table. Incoming and outgoing healing are separate inputs
that add, following [TCL Healing](https://library.keqingmains.com/combat-mechanics/damage/healing).
Shield absorption includes the talent's flat term and the active recipient's
shield strength, following [TCL Shields](https://library.keqingmains.com/combat-mechanics/damage/shields).

## Character and role coverage matrix

`partial-draft` means at least one event definition exists; the remaining roles
are still gaps. Every role without a matching definition is a **research candidate**,
not a sourced claim that the role is viable or an assertion of full coverage.
The role plan preserves niche possibilities for review instead of assigning
unresearched numerical defaults. Older guides' stated versions remain recorded;
Fischl's 4.0 and Jean's 4.0 guides, for example, do not establish current full-kit
coverage. No set is marked obsolete just because it lacks an optimal build.

| GOOD character key | Element | Status | Roles requiring or receiving research |
| --- | --- | --- | --- |
| Aino | hydro | unresearched | hydro-application, lunar-team-support |
| Albedo | geo | partial-draft | off-field-damage (event draft), hexerei-team-support, lunar-crystallize, burst-damage |
| Alhaitham | dendro | unresearched | on-field-spread, quickbloom-driver |
| Aloy | cryo | unresearched | burst-damage, on-field-cryo |
| Alyosha | electro | unresearched | stellar-team-support |
| Amber | pyro | unresearched | charged-shot-damage, burst-support, burgeon-trigger |
| AratakiItto | geo | unresearched | on-field-def-conversion |
| Arlecchino | pyro | unresearched | on-field-vaporize, on-field-mono-pyro, overloaded-carry |
| Baizhu | dendro | unresearched | healing, dendro-team-support, on-field-driver |
| Barbara | hydro | partial-draft | healing (event draft), vaporize-charged-damage, bloom-trigger, clam-driver |
| Beidou | electro | unresearched | off-field-burst, aggravate, defensive-support |
| Bennett | pyro | unresearched | healing-atk-support, on-field-pyro, reaction-driver |
| Candace | hydro | unresearched | hydro-infusion-support, bloom-trigger, on-field-damage |
| Charlotte | cryo | unresearched | healing, cryo-application-support |
| Chasca | anemo | unresearched | multi-element-charged-damage |
| Chevreuse | pyro | unresearched | overloaded-team-support, healing, burst-damage |
| Chiori | geo | unresearched | mixed-atk-def-off-field-damage |
| Chongyun | cryo | unresearched | cryo-infusion-support, reverse-melt-burst |
| Citlali | cryo | unresearched | em-shielding, pyro-hydro-team-support |
| Clorinde | electro | unresearched | on-field-aggravate, quickbloom, overloaded |
| Collei | dendro | unresearched | off-field-dendro-support, bloom-trigger, spread-damage |
| Columbina | hydro | unresearched | lunar-reaction-conversion, lunar-team-support, off-field-damage |
| Cyno | electro | unresearched | on-field-aggravate, quickbloom |
| Dahlia | hydro | unresearched | shielding, attack-speed-support |
| Dehya | pyro | unresearched | defensive-support, burgeon-trigger, burst-damage |
| Diluc | pyro | unresearched | on-field-vaporize, plunge-vaporize, melt |
| Diona | cryo | unresearched | shielding, healing-battery, em-team-support |
| Dori | electro | unresearched | healing-energy-support, hyperbloom-trigger, on-field-driver |
| Durin | pyro | unresearched | hexerei-off-field-damage, resistance-support |
| Emilie | dendro | unresearched | burning-off-field-damage |
| Escoffier | cryo | unresearched | off-field-cryo-damage, healing-resistance-support |
| Eula | cryo | unresearched | physical-burst-damage |
| Faruzan | anemo | unresearched | anemo-team-support, on-field-anemo, swirl-trigger |
| Fischl | electro | partial-draft | off-field-damage (event draft), aggravate, on-field-physical, hexerei-support |
| Flins | electro | unresearched | on-field-lunar-charged |
| Freminet | cryo | unresearched | physical-shatter, on-field-cryo |
| Furina | hydro | unresearched | hp-off-field-damage, fanfare-team-support, healing |
| Gaming | pyro | unresearched | plunge-vaporize, plunge-melt |
| Ganyu | cryo | unresearched | charged-freeze, charged-melt, burst-support |
| Gorou | geo | unresearched | def-geo-team-support, healing |
| HuTao | pyro | unresearched | hp-atk-conversion-vaporize, plunge-vaporize |
| Iansan | electro | unresearched | atk-team-support, healing |
| Ifa | anemo | unresearched | swirl-driver, reaction-team-support, healing |
| Illuga | geo | unresearched | lunar-crystallize-support |
| Ineffa | electro | unresearched | shielding, lunar-charged-support |
| Jahoda | anemo | unresearched | healing, anemo-support |
| Jean | anemo | partial-draft | general-healing-support, sunfire-trigger (event draft), on-field-damage |
| Kachina | geo | unresearched | def-off-field-damage, scroll-team-support |
| KaedeharaKazuha | anemo | unresearched | swirl-em-support, aggravated-swirl, on-field-damage |
| Kaeya | cryo | unresearched | off-field-freeze, reverse-melt, on-field-physical |
| KamisatoAyaka | cryo | partial-draft | quickswap-damage (event draft), on-field-cryo |
| KamisatoAyato | hydro | unresearched | on-field-hydro, reaction-driver, burst-support |
| Kaveh | dendro | unresearched | bloom-driver, bloom-trigger |
| Keqing | electro | unresearched | on-field-aggravate, electro-damage, physical-damage |
| Kinich | dendro | unresearched | burning-skill-damage, burgeon-skill-damage |
| Kirara | dendro | unresearched | shielding, on-field-dendro-application, burst-damage |
| Klee | pyro | unresearched | on-field-pyro, burgeon-trigger, hexerei-support |
| KujouSara | electro | unresearched | electro-atk-support, burst-damage |
| KukiShinobu | electro | partial-draft | hyperbloom-trigger (event draft), healing (event draft), quicken-support |
| LanYan | anemo | unresearched | atk-shielding, swirl-driver, anemo-team-support |
| Lauma | dendro | unresearched | lunar-bloom-support, em-reaction-support |
| Layla | cryo | unresearched | shielding, off-field-cryo-damage |
| Linnea | geo | unresearched | lunar-crystallize-off-field, healing-support |
| Lisa | electro | unresearched | aggravate, defense-shred-support, hyperbloom-trigger |
| Lohen | cryo | unresearched | kit-and-role-research |
| Lynette | anemo | unresearched | anemo-support, on-field-driver, hyperbloom-swirl |
| Lyney | pyro | unresearched | mono-pyro-charged-damage |
| Mavuika | pyro | unresearched | on-field-vaporize, on-field-melt, off-field-pyro-support |
| Mika | cryo | unresearched | physical-team-support, healing |
| Mona | hydro | unresearched | omen-support, vaporize-burst, hydro-driver, prototype-amber-healer |
| Mualani | hydro | unresearched | hp-skill-vaporize |
| Nahida | dendro | partial-draft | off-field-damage (event draft), on-field-driver, em-team-support, bloom-trigger |
| Navia | geo | unresearched | crystallize-skill-damage, quick-swap-damage |
| Nefer | dendro | unresearched | on-field-lunar-bloom |
| Neuvillette | hydro | partial-draft | on-field-damage (event draft), vaporize, lunar-reaction-driver |
| Nicole | pyro | unresearched | hexerei-team-support |
| Nilou | hydro | unresearched | hp-bountiful-core-support, bloom-trigger, hydro-damage |
| Ningguang | geo | unresearched | on-field-geo, quickswap-burst, petra-support |
| Noelle | geo | unresearched | def-conversion-on-field, healing, shielding, favonius-driver |
| Odette | cryo | unresearched | stellar-reaction-support |
| Ororon | electro | unresearched | electro-charged-off-field, scroll-team-support, hyperbloom-trigger |
| Prune | anemo | unresearched | kit-and-role-research |
| Qiqi | cryo | unresearched | healing, clam-driver, physical-damage |
| RaidenShogun | electro | partial-draft | hyperbloom-trigger (event draft), overloaded-trigger, on-field-burst, on-field-aggravate, team-energy-support |
| Razor | electro | unresearched | physical-damage, aggravate, mixed-reaction-driver |
| Rosaria | cryo | unresearched | reverse-melt, freeze-off-field, crit-team-support, physical-damage |
| Sandrone | cryo | unresearched | kit-and-role-research |
| SangonomiyaKokomi | hydro | unresearched | healing, on-field-hp-damage, bloom-trigger, clam-driver, tenacity-support |
| Sayu | anemo | unresearched | atk-em-healing, swirl-driver, anemo-support |
| Sethos | electro | unresearched | em-charged-aggravate, burst-aggravate |
| Shenhe | cryo | unresearched | atk-cryo-quill-support, burst-support |
| ShikanoinHeizou | anemo | unresearched | anemo-damage, swirl-driver, em-support |
| Sigewinne | hydro | unresearched | healing, off-field-skill-support, hp-burst-damage |
| Skirk | cryo | unresearched | normal-cryo-damage, quickswap-cryo-burst |
| Somnia | electro | unresearched | kit-and-role-research |
| Sucrose | anemo | unresearched | on-field-swirl-driver, off-field-em-support, aggravated-swirl, hyperbloom-swirl, hexerei-support |
| Tartaglia | hydro | unresearched | on-field-hydro-driver, vaporize-burst |
| Thoma | pyro | partial-draft | burgeon-trigger (event draft), shielding, team-support |
| Tighnari | dendro | unresearched | charged-spread |
| Traveler | variable | unresearched | anemo/swirl-support, anemo/anemo-damage, geo/geo-damage, geo/crit-team-support, electro/energy-support, electro/hyperbloom-trigger, dendro/dendro-application-support, dendro/spread-damage, hydro/hydro-damage, hydro/hydro-application, pyro/scroll-support, pyro/burgeon-trigger, pyro/pyro-damage, cryo/stellar-reaction-support, cryo/kit-and-role-research |
| Varesa | electro | unresearched | plunge-electro-damage |
| Varka | anemo | unresearched | on-field-multi-element, hexerei-team-support |
| Venti | anemo | unresearched | swirl-support, crit-anemo-damage, on-field-hexerei |
| Wanderer | anemo | unresearched | normal-charged-anemo-damage |
| Wriothesley | cryo | unresearched | on-field-freeze, on-field-melt, stellar-conduct |
| Xiangling | pyro | unresearched | off-field-vaporize, reverse-melt, mono-pyro, burning-support, burgeon-trigger |
| Xianyun | anemo | unresearched | atk-healing-plunge-support, on-field-plunge |
| Xiao | anemo | unresearched | plunge-anemo-damage |
| Xilonen | geo | unresearched | def-healing-resistance-support, on-field-geo-damage |
| Xingqiu | hydro | partial-draft | off-field-damage (event draft), on-field-hydro, team-support, bloom-trigger |
| Xinyan | pyro | unresearched | def-shielding, physical-burst, pyro-damage |
| YaeMiko | electro | unresearched | aggravate-off-field, skill-burst-electro, on-field-driver, stellar-reactions |
| Yanfei | pyro | unresearched | charged-vaporize, overloaded, shielding |
| Yaoyao | dendro | partial-draft | healing (event draft), dendro-team-support, bloom-trigger, spread-damage |
| Yelan | hydro | partial-draft | off-field-damage (event draft), on-field-hydro, team-support |
| Yoimiya | pyro | unresearched | normal-vaporize, overloaded, mono-pyro |
| YumemizukiMizuki | anemo | unresearched | swirl-driver, em-healing |
| YunJin | geo | unresearched | def-normal-attack-support |
| Zhongli | geo | partial-draft | shielding (event draft), burst-damage, team-support, physical-damage |
| Zibai | geo | unresearched | on-field-lunar-crystallize |
| Vesna (GOOD key unverified) | unverified | guide-index-only | Index has a 7.1 guide; no GOOD key or stats in pinned GO snapshot. Release availability and kit require primary guide review. |
| Vodyanitsa (GOOD key unverified) | unverified | guide-index-only | Index has a 7.1 guide; no GOOD key or stats in pinned GO snapshot. Release availability and kit require primary guide review. |

## Artifact set coverage matrix

Seven sets have their relevant event bonuses encoded, fifteen have partial
effects, and forty-one have no encoded effects. All remain draft. An unused
four-piece effect is still a coverage gap even when the two-piece bonus works.
For example, Clam's healing bonus does not implement its accumulation damage;
Noblesse's Burst bonus does not implement teammate utility. The runtime can
inspect incomplete compositions; it does not infer that uncovered sets are safe
to delete. Non-five-star sets, especially Instructor and Exile support, remain
explicit research needs and have enhancement/search limitations.

| GOOD set key | Available rarities | Encoding status | Remaining support |
| --- | --- | --- | --- |
| ResolutionOfSojourner | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| BraveHeart | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| DefendersWill | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| TinyMiracle | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| Berserker | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| MartialArtist | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| Instructor | 3, 4 | unresearched | Niche on-field reaction support; four-star stats and team EM buff require dedicated support coverage. |
| Gambler | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| TheExile | 3, 4 | unresearched | Niche team energy support; four-star enhancement and teammate energy utility remain unsupported. |
| Adventurer | 1, 2, 3 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| LuckyDog | 1, 2, 3 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| Scholar | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| TravelingDoctor | 1, 2, 3 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| BlizzardStrayer | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| Thundersoother | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| Lavawalker | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| MaidenBeloved | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| GladiatorsFinale | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| ViridescentVenerer | 4, 5 | partial-effects | Single Swirl event and a preexisting resistance debuff are modeled; multi-target limits and teammate utility remain gaps. |
| WanderersTroupe | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| ThunderingFury | 4, 5 | partial-effects | Electro bonus and Hyperbloom bonus only; other reactions and cooldown resets remain gaps. |
| CrimsonWitchOfFlames | 4, 5 | partial-effects | Pyro two-piece and Burgeon bonus only; amplifying reactions and Skill stacks remain gaps. |
| NoblesseOblige | 4, 5 | partial-effects | Four-piece team ATK utility and Burst snapshot timing are not modeled. |
| BloodstainedChivalry | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| PrayersForIllumination | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| PrayersForDestiny | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| PrayersForWisdom | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| PrayersToSpringtime | 3, 4 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ArchaicPetra | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| RetracingBolide | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| HeartOfDepth | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| TenacityOfTheMillelith | 4, 5 | partial-effects | Holder ATK and recipient shield strength are encoded; teammate ATK utility and uptime are not scored. |
| PaleFlame | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ShimenawasReminiscence | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| EmblemOfSeveredFate | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| HuskOfOpulentDreams | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| OceanHuedClam | 4, 5 | partial-effects | Four-piece accumulation, overflow healing, shared bubble limits, physical resistance and event timing are not modeled. |
| VermillionHereafter | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| EchoesOfAnOffering | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| DeepwoodMemories | 4, 5 | partial-effects | Dendro bonus and active resistance debuff are modeled; teammate utility and multi-wave timing remain gaps. |
| GildedDreams | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| DesertPavilionChronicle | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| FlowerOfParadiseLost | 4, 5 | partial-effects | Bloom/Hyperbloom/Burgeon samples are encoded; Lunar-Bloom, initial stack timing and ICD event traces require reference checks. |
| NymphsDream | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| VourukashasGlow | 4, 5 | partial-effects | Two-piece only; four-piece role/effects require research. |
| MarechausseeHunter | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| GoldenTroupe | 4, 5 | draft-event-subset | Activation snapshots and complete rotations need independent game checks. |
| SongOfDaysPast | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| NighttimeWhispersInTheEchoingWoods | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| FragmentOfHarmonicWhimsy | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| UnfinishedReverie | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ScrollOfTheHeroOfCinderCity | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ObsidianCodex | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| LongNightsOath | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| FinaleOfTheDeepGalleries | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| NightOfTheSkysUnveiling | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| SilkenMoonsSerenade | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| AubadeOfMorningstarAndMoon | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ADayCarvedFromRisingWinds | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| CelestialGift | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| DisenchantmentInDeepShadow | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| ScarletProof | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |
| HeartOfTheFurnace | 4, 5 | unresearched | No executable effect coverage. Naming this key in mechanics does not implement its effects. |

## Prospects and unsupported calculations

The five complete structural drafts are generic HP/Cryo freeze damage, mixed
ATK/HP Cryo damage, DEF/Geo Skill damage, ATK healing, and DEF healing. Their
bases and coefficients are explicitly assumed, with their own archetype
families and no invented named future character. Parameter variants instead
sample ER endpoints, expired activations, HP states, set stacks, flat buffs,
and external resistance reduction while inheriting their parent's family.

Remaining work includes complete rotations; on-field alternatives; reverse
Vaporize and Aggravate event mixes; DEF/HP-to-ATK conversions; teammate support
objectives; healing accumulation and overheal utility; and Lunar, Stellar and
newer Hexerei team mechanics. The coverage JSON proposes ordered-event and
team-objective capabilities with units, dependencies, semantics and reference
cases. Neither capability is advertised as an installed expression extension.
Unsupported roles must stay visible gaps in downstream coverage policy.

## Validation and ranking assumptions

The checked release compiles 78 scenarios. The report records 91 component
reference cases, 13 formula reference cases and 204 aggregate event checks.
Checks include capped crit, ER-to-Burst caps, negative/high resistance branches,
healing and shield terms, EM curves, HP-derived bonuses, set counts and
inheritance. Incomplete set fixtures remain infeasible coverage needs, and
publication gating rejects the draft batch. The targeted pytest run passed
73 tests. Black formatted the new Python files. No type-checker run is claimed.

The scalar checks use an independent arithmetic expression of the documented
rules, but aggregate score checks use the engine's reported effective totals.
They do not compare against independently verified legal five-artifact builds
in-game or in GO. The report marks `game_validated: false`, all research statuses
remain `draft`, and the mechanics manifest has `validated: false`.

The assumptions with the largest likely ranking effects are:

- Level 90/A6, concrete level-90 weapons, talent level 10 and C0 baselines; passive
  refinements/conditions are explicit. Weapon alternatives are not exhaustive.
- ER cases depend on the stated Skill count, assumed Favonius procs, constellations,
  team and rotation. Guide endpoints are samples, not account energy guarantees.
  Ayaka's 1.40 and higher sensitivity case are explicitly assumed energy targets.
- Set stacks and activation are event snapshots. Gilded's triggering event,
  Paradise stack acquisition, Hunter pre-stacking and Golden's grace window
  need timing checks before full-rotation rankings can be trusted.
- Enemy level 100, resistance 0.10, and absent external buffs are reference target
  assumptions. External Deepwood is explicitly sampled instead of counted twice.
- Neuvillette's HP fractions are individual events, not average HP; Albedo's
  Hexerei addition is established but its teammate buff is still omitted.
- Healing scores are single received heals and shields are absorption events;
  healing sufficiency, shield uptime and teammate damage are separate gaps.

Do not interpret this partial batch as exhaustive deletion coverage. Source
prose, revision labels and successful parser checks cannot establish deletion
safety. The existing runtime's expanded numerical content and pinned mechanics
provide cache identity; these artifacts introduce no ownership filters,
retention weights, deletion budgets or GUI changes.
