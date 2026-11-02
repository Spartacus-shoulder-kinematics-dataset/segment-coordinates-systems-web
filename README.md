# ISB coordinate systems, in 3D

A static website that explains the ISB recommendations for segment (LCS) and joint (JCS) coordinate systems
(Wu et al. 2002, Wu et al. 2005, and the knee via Grood & Suntay 1983). Each segment frame is built step by
step on real bone meshes, and each joint has a playground with e1/e2/e3, angle arcs, left/right handling and
a comparison of the same pose across the 12 rotation sequences.

## Build and run

```bash
conda run -n spartacus python build.py                    # -> site/
conda run -n spartacus python -m http.server -d site 8000 # open http://localhost:8000
conda run -n spartacus pytest -q                          # geometry, signs, left side, JS parity, SPARTACUS parity
```

`build.py --vendor` downloads Three.js into the site instead of loading it from jsDelivr.
The pages use ES modules, so open them through a web server (e.g. GitHub Pages), not as `file://`.

## Layout

- `isb/`: the single source of truth (Python)
  - `definitions/`: every segment and joint, one declarative file per region
  - `geometry.py`, `rotations.py`, `sides.py`: construction evaluation, Euler/Cardan sequences, left side
  - `landmarks.py`: landmark metadata; positions come from `isb/data/landmarks.json`
  - `export.py`: JSON for the site (construction steps, both sides, neutral angles, formulas)
- `templates/`, `static/`: Jinja pages, CSS, Three.js viewers (`static/js`)
- `tools/prepare_meshes.py`: builds `static/meshes/*.bin` and detects the landmarks on the bones
- `tests/`: pytest suite; `tests/js/rotations.test.mjs` checks `rotations.js` against scipy

## Bone meshes and landmarks

The meshes and landmark positions come from **BodyParts3D, © The Database Center for Life Science, licensed
under CC Attribution 4.0 International** (https://lifesciencedb.jp/bp3d/). The OBJ files themselves cite
CC BY-SA 2.1 JP; the derived meshes in `static/meshes/` (axis change to the ISB frame, decimation) are shared
under the same terms. See `static/meshes/LICENSE.txt`.

To regenerate them (downloads ~62 MB into `.cache/`; decimation uses `fast-simplification`, installed locally):

```bash
conda run -n spartacus python -m pip install --target .cache/pydeps fast-simplification
rm -rf .cache/pydeps/numpy*        # keep the environment's numpy
conda run -n spartacus python tools/prepare_meshes.py
```

The landmarks are detected automatically (extreme points, sphere fits for the hip and glenohumeral centres,
surface normals for the vertebral endplates). They were checked visually, but they are not expert digitisations.

## Accuracy

Recommendation texts are paraphrased. Items the site marks "Verify against the paper" are uncertain and should
be checked against the PDFs of Wu et al. 2002 and 2005.
