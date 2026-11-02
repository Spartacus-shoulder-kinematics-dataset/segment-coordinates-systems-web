"""Build the static site into ./site.

    conda run -n spartacus python build.py            # Three.js from the jsDelivr CDN
    conda run -n spartacus python build.py --vendor   # download Three.js into site/static/vendor (offline use)
    conda run -n spartacus python -m http.server -d site 8000
"""

import argparse
import json
import shutil
import urllib.request
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from isb.export import build_dataset, region_subset

ROOT = Path(__file__).resolve().parent
THREE_VERSION = "0.170.0"
THREE_CDN = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}"
THREE_FILES = (
    "build/three.module.js",
    "build/three.core.js",
    "examples/jsm/controls/OrbitControls.js",
    "examples/jsm/renderers/CSS2DRenderer.js",
)


def option_groups(keys, segments):
    """Consecutive segments sharing an option_group become one card with tabs."""
    groups = []
    for k in keys:
        g = segments[k]["option_group"]
        if groups and g and segments[groups[-1][0]]["option_group"] == g:
            groups[-1].append(k)
        else:
            groups.append([k])
    return groups


def vendor_three(out: Path) -> str:
    base = out / "static" / "vendor" / f"three@{THREE_VERSION}"
    for rel in THREE_FILES:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(f"{THREE_CDN}/{rel}", timeout=30) as r:
                target.write_bytes(r.read())
        except urllib.error.HTTPError as e:
            if rel.endswith("three.core.js") and e.code == 404:
                continue  # only split into core + module in later releases
            raise
    return f"static/vendor/three@{THREE_VERSION}"


def build(out: Path, vendor: bool) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "static", out / "static")
    three_url = vendor_three(out) if vendor else THREE_CDN

    data = build_dataset()
    (out / "data").mkdir()
    (out / "data" / "isb.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True, undefined=StrictUndefined)
    env.filters["ref_short"] = lambda key: data["references"][key]["short"]
    common = {"regions": data["regions"], "references": data["references"], "three_url": three_url}

    def render(template: str, filename: str, **ctx):
        html = env.get_template(template).render(**common, **ctx)
        (out / filename).write_text(html)

    render(
        "index.html",
        "index.html",
        page="index",
        page_title="Home",
        description="Interactive 3D explorer of the ISB segment (LCS) and joint (JCS) coordinate system recommendations.",
    )
    render(
        "concepts.html",
        "concepts.html",
        page="concepts",
        page_title="Concepts",
        description="LCS, JCS, floating axis, Euler/Cardan sequences, gimbal lock, signs and the left side.",
    )
    render(
        "sequences.html",
        "sequences.html",
        page="sequences",
        page_title="Rotation sequences",
        description="The 12 intrinsic Euler/Cardan sequences, intermediate frames and gimbal lock.",
    )
    region_titles = {r["key"]: r["title"] for r in data["regions"]}
    render(
        "reference.html",
        "reference.html",
        page="reference",
        page_title="Reference tables",
        description="All ISB segment and joint coordinate systems in one table.",
        segment_rows=list(data["segments"].values()),
        joint_rows=list(data["joints"].values()),
        landmarks=data["landmarks"],
        region_titles=region_titles,
        segment_names={k: s["name"] + (f" ({s['option_label']})" if s["option_label"] else "") for k, s in data["segments"].items()},
    )
    for region in data["regions"]:
        subset = region_subset(data, region["key"])
        render(
            "region.html",
            f"{region['key']}.html",
            page=region["key"],
            page_title=region["title"],
            description=region["intro"],
            region=region,
            segments=subset["segments"],
            joints=subset["joints"],
            landmarks=subset["landmarks"],
            groups=option_groups(region["segments"], subset["segments"]),
            data_json=json.dumps(subset, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        )
    print(f"Built {len(list(out.glob('*.html')))} pages into {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ROOT / "site")
    parser.add_argument("--vendor", action="store_true", help="download Three.js instead of using the CDN")
    args = parser.parse_args()
    build(args.out, args.vendor)
