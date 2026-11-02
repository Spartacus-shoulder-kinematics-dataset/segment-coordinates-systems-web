from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, sub, unit


def vertebra(v: str) -> SegmentCS:
    return SegmentCS(
        key=v,
        name=f"{v} vertebra",
        region="spine",
        reference="wu2002",
        section="Spine, vertebral local coordinate system",
        axes_text={
            "o": "Centroid of the vertebral body.",
            "Y": "Parallel to the line joining the centres of the inferior and superior endplates, pointing "
            "cranially.",
            "Z": "Parallel to the line joining bilateral landmarks (e.g. the bases of the pedicles), orthogonal to "
            "Y, pointing to the right.",
            "X": "Perpendicular to Y and Z, pointing anteriorly.",
        },
        steps=(
            Step("o", f"{v}_c", "The origin is the centroid of the vertebral body.", kind="origin"),
            Step("Y", unit(sub(f"{v}_ue", f"{v}_le")), "Y goes from the inferior to the superior endplate centre."),
            Step(
                "b",
                unit(sub(f"{v}_rp", f"{v}_lp")),
                "Bilateral direction from the left to the right pedicle base.",
            ),
            Step("X", unit(cross("Y", "b")), "X is perpendicular to Y and the bilateral line, pointing anteriorly."),
            Step("Z", cross("X", "Y"), "Z completes the triad: orthogonal to Y, close to the bilateral line, to the right."),
        ),
        landmarks=(f"{v}_c", f"{v}_ue", f"{v}_le", f"{v}_rp", f"{v}_lp"),
        meshes=(v,),
        links=((f"{v}_ue", f"{v}_le"), (f"{v}_rp", f"{v}_lp"), (f"{v}_c", f"{v}_rp"), (f"{v}_c", f"{v}_lp")),
        planes=((f"{v}_ue", f"{v}_rp", f"{v}_lp"),),
        needs_check=("Landmarks used for Y (endplate centres) and for the bilateral direction (pedicle bases).",),
        view=(0.5, 0.35, 1.0),
    )


SPINE_ANGLES = (
    AngleDef("Flexion / extension", "extension", "flexion", (-30, 30), "By the right-hand rule about a Z axis pointing "
             "right, a positive rotation tilts the upper vertebra backwards (extension)."),
    AngleDef("Lateral bending", "right lateral bending", "left lateral bending", (-30, 30)),
    AngleDef("Axial rotation", "left axial rotation", "right axial rotation", (-30, 30),
             "A positive rotation about Y (up) turns the anterior surface to the left."),
)


def motion_segment(upper: str, lower: str, name: str) -> JointCS:
    return JointCS(
        key=f"{upper}_{lower}",
        name=f"{name} ({upper} relative to {lower})",
        region="spine",
        reference="wu2002",
        section="Spine JCS",
        parent=lower,
        child=upper,
        sequence="ZXY",
        angles=SPINE_ANGLES,
        view=(0.5, 0.35, 1.0),
        axes_text={
            "e1": f"Z axis of the inferior vertebra ({lower}).",
            "e2": "Floating axis, the common perpendicular of e1 and e3.",
            "e3": f"Y axis of the superior vertebra ({upper}).",
        },
        translations=(
            "Translations of the upper vertebral centroid relative to the lower one along e1 (lateral shear), "
            "e2 (anterior-posterior shear) and e3 (axial compression-distraction)."
        ),
        notes=(
            "The rotation names are those of the right-hand rule with X anterior, Y cranial, Z right; the sign "
            "is the same for every spinal level.",
        ),
        needs_check=(
            "Which vertebra is proximal (here the inferior one) and the sign naming of the three rotations.",
        ),
    )


SEGMENTS = tuple(vertebra(v) for v in ("C4", "C5", "T7", "T8", "L4", "L5"))
JOINTS = (
    motion_segment("C4", "C5", "Cervical"),
    motion_segment("T7", "T8", "Thoracic"),
    motion_segment("L4", "L5", "Lumbar"),
)

REGION = Region(
    key="spine",
    title="Spine",
    references=("wu2002",),
    intro=(
        "Wu et al. (2002) define a local frame for each vertebra, centred on the vertebral body, and a JCS between "
        "adjacent vertebrae: flexion/extension about the Z axis of the inferior vertebra, axial rotation about the "
        "Y axis of the superior vertebra, and lateral bending about the floating axis. The spine is a midline "
        "structure, so there is no left/right toggle."
    ),
    segments=tuple(s.key for s in SEGMENTS),
    joints=tuple(j.key for j in JOINTS),
    notes=(
        "Wu et al. (2002) also discuss a global frame and the head/pelvis frames used to report regional spinal "
        "motion; only the vertebral frames and intervertebral JCS are shown here.",
    ),
    sided=False,
)
