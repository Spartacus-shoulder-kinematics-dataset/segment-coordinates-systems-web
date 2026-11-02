from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, mid, reject, sub, unit

pelvis = SegmentCS(
    key="pelvis",
    name="Pelvis",
    region="hip",
    reference="wu2002",
    section="Hip joint, pelvic coordinate system (XYZ)",
    axes_text={
        "o": "The (right) hip joint centre.",
        "Z": "Line parallel to the line connecting the right and left ASISs, pointing to the right.",
        "X": "Line parallel to a line lying in the plane defined by the two ASISs and the midpoint of the two "
        "PSISs, orthogonal to Z, pointing anteriorly.",
        "Y": "Line perpendicular to X and Z, pointing cranially.",
    },
    steps=(
        Step("o", "HJC", "The origin is the hip joint centre of the side being studied.", kind="origin"),
        Step("mPSIS", mid("RPSIS", "LPSIS"), "Midpoint of the two PSISs.", kind="point"),
        Step("mASIS", mid("RASIS", "LASIS"), "Midpoint of the two ASISs.", kind="point"),
        Step("Z", unit(sub("RASIS", "LASIS")), "Z is parallel to LASIS→RASIS, so it points to the right."),
        Step(
            "v",
            sub("mASIS", "mPSIS"),
            "A line lying in the ASIS/mid-PSIS plane and pointing anteriorly.",
        ),
        Step(
            "X",
            unit(reject("v", "Z")),
            "Remove the Z component so that X is orthogonal to Z while staying in the pelvic plane.",
        ),
        Step("Y", cross("Z", "X"), "Y completes the triad and points cranially."),
    ),
    landmarks=("RASIS", "LASIS", "RPSIS", "LPSIS", "HJC"),
    meshes=("pelvis",),
    view=(1.0, 0.8, 0.6),
    links=(("RASIS", "LASIS"), ("RPSIS", "LPSIS"), ("RASIS", "RPSIS"), ("LASIS", "LPSIS")),
    planes=(("RASIS", "LASIS", "mPSIS"),),
    notes=(
        "The pelvic frame is anatomical (ASIS/PSIS based) but its origin is the hip joint centre, so the "
        "pelvis has one frame per hip, sharing the same axes.",
        "Pelvic tilt: in a typical standing posture the ASIS/PSIS plane is tilted, so Y is not vertical.",
    ),
)

femur = SegmentCS(
    key="femur",
    name="Femur",
    region="hip",
    reference="wu2002",
    section="Hip joint, femoral coordinate system (xyz)",
    axes_text={
        "o": "The hip joint centre, coincident with the pelvic origin in the neutral configuration.",
        "Y": "Line joining the midpoint between the medial and lateral femoral epicondyles and the origin, "
        "pointing cranially.",
        "Z": "Line perpendicular to Y, lying in the plane defined by the origin and the two femoral epicondyles, "
        "pointing to the right.",
        "X": "Line perpendicular to both Y and Z, pointing anteriorly.",
    },
    steps=(
        Step("o", "HJC", "The origin is the hip joint centre.", kind="origin"),
        Step("mFE", mid("LFE", "MFE"), "Midpoint of the femoral epicondyles.", kind="point"),
        Step("Y", unit(sub("HJC", "mFE")), "Y is the mechanical axis of the femur, pointing up to the HJC."),
        Step(
            "Z",
            unit(reject(sub("LFE", "MFE"), "Y")),
            "Take the epicondylar line (medial→lateral, i.e. to the right for a right femur) and remove its Y "
            "component: the result lies in the (HJC, FE₁, FE₂) plane, perpendicular to Y.",
        ),
        Step("X", cross("Y", "Z"), "X completes the triad and points anteriorly."),
    ),
    landmarks=("HJC", "LFE", "MFE"),
    meshes=("femur", "patella"),
    links=(("HJC", "LFE"), ("HJC", "MFE"), ("LFE", "MFE")),
    planes=(("HJC", "LFE", "MFE"),),
    notes=(
        "Y is the mechanical axis (HJC to knee centre), not the anatomical shaft axis.",
        "Using the plane (HJC, FE₁, FE₂) makes the frame sensitive to femoral anteversion only through the "
        "epicondyles, not through the femoral neck.",
    ),
)

hip = JointCS(
    key="hip",
    name="Hip joint",
    region="hip",
    reference="wu2002",
    section="Hip joint JCS",
    parent="pelvis",
    child="femur",
    sequence="ZXY",
    angles=(
        AngleDef("Flexion / extension", "flexion", "extension", (-40, 130)),
        AngleDef("Adduction / abduction", "adduction", "abduction", (-50, 40)),
        AngleDef("Internal / external rotation", "internal rotation", "external rotation", (-60, 60)),
    ),
    axes_text={
        "e1": "Z axis of the pelvis (fixed in the pelvis).",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the femur (fixed in the femur).",
    },
    translations=(
        "Translations of the femoral origin relative to the pelvic origin along e1, e2 and e3. With both origins "
        "at the hip joint centre they are zero for an ideal ball joint."
    ),
    notes=(
        "In the neutral configuration the femoral and pelvic frames coincide, so all angles are zero. With "
        "real landmarks (pelvic tilt, femoral adduction) the anatomical posture gives small non-zero angles.",
    ),
)

REGION = Region(
    key="hip",
    title="Hip",
    references=("wu2002",),
    intro=(
        "The pelvis frame is built from the four iliac spines with its origin at the hip joint centre; the "
        "femur frame from the hip joint centre and the femoral epicondyles. The hip JCS is the Grood & Suntay "
        "construction: flexion about the pelvic Z, adduction about the floating axis, rotation about the femoral Y."
    ),
    segments=("pelvis", "femur"),
    joints=("hip",),
)

SEGMENTS = (pelvis, femur)
JOINTS = (hip,)
