from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, sub, unit


EXTRA_MESHES = {"MC3": ("carpus",), "MP2": ("DP2",)}


def hand_bone(b: str, name: str) -> SegmentCS:
    return SegmentCS(
        key=b,
        name=name,
        region="wrist",
        reference="wu2005",
        section="Hand, generic bone coordinate system",
        axes_text={
            "o": "Centre of the base of the bone.",
            "Y": "Line parallel to the shaft, from the centre of the head to the centre of the base, pointing "
            "proximally.",
            "X": "Perpendicular to Y, pointing volarly (anteriorly in the anatomical position).",
            "Z": "Perpendicular to X and Y, pointing radially (to the right for the right hand).",
        },
        steps=(
            Step("o", f"{b}_b", "The origin is the centre of the base.", kind="origin"),
            Step("Y", unit(sub(f"{b}_b", f"{b}_h")), "Y runs along the shaft from the head to the base."),
            Step(
                "r",
                unit(sub(f"{b}_hr", f"{b}_hu")),
                "Radioulnar direction across the head, from the ulnar to the radial side.",
            ),
            Step("X", unit(cross("Y", "r")), "X is perpendicular to the shaft and to the radioulnar line: volar."),
            Step("Z", cross("X", "Y"), "Z completes the triad, pointing radially."),
        ),
        landmarks=(f"{b}_b", f"{b}_h", f"{b}_hr", f"{b}_hu"),
        meshes=(b,) + EXTRA_MESHES.get(b, ()),
        links=((f"{b}_b", f"{b}_h"), (f"{b}_hr", f"{b}_hu")),
        needs_check=(
            "Origin (base centre assumed) and the landmarks that fix X/Z for the hand bones.",
        ),
    )


mc3 = hand_bone("MC3", "Third metacarpal")
mc2 = hand_bone("MC2", "Second metacarpal")
pp2 = hand_bone("PP2", "Proximal phalanx (index)")
mp2 = hand_bone("MP2", "Middle phalanx (index)")

FINGER_ANGLES = (
    AngleDef("Flexion / extension", "flexion", "extension", (-30, 110)),
    AngleDef("Ulnar / radial deviation", "ulnar deviation", "radial deviation", (-30, 30),
             "For the index finger, ulnar deviation is adduction (towards the middle finger)."),
    AngleDef("Axial rotation", "pronation", "supination", (-30, 30)),
)

wrist = JointCS(
    key="wrist",
    name="Wrist (radiocarpal + midcarpal)",
    region="wrist",
    reference="wu2005",
    section="Wrist JCS",
    parent="radius",
    child="MC3",
    sequence="ZXY",
    angles=(
        AngleDef("Flexion / extension", "flexion", "extension", (-70, 80)),
        AngleDef("Ulnar / radial deviation", "ulnar deviation", "radial deviation", (-20, 40)),
        AngleDef("Pronation / supination", "pronation", "supination", (-20, 20)),
    ),
    axes_text={
        "e1": "Z axis of the radius.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the third metacarpal (the hand).",
    },
    notes=(
        "The third metacarpal represents the whole hand: the carpal bones are not tracked individually.",
    ),
    needs_check=("Radius frame used for the wrist (the RS-origin radius frame of the elbow page is reused here).",),
)

mcp2 = JointCS(
    key="mcp2",
    name="MCP joint (index)",
    region="wrist",
    reference="wu2005",
    section="Hand, MCP JCS",
    parent="MC2",
    child="PP2",
    sequence="ZXY",
    angles=FINGER_ANGLES,
    axes_text={
        "e1": "Z axis of the metacarpal.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the proximal phalanx.",
    },
    notes=("The same generic JCS applies to every CMC, MCP and IP joint of the fingers.",),
)

pip2 = JointCS(
    key="pip2",
    name="PIP joint (index)",
    region="wrist",
    reference="wu2005",
    section="Hand, IP JCS",
    parent="PP2",
    child="MP2",
    sequence="ZXY",
    angles=FINGER_ANGLES,
    axes_text={
        "e1": "Z axis of the proximal phalanx.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the middle phalanx.",
    },
    notes=("Interphalangeal joints are essentially hinges: the second and third angles stay small.",),
)

REGION = Region(
    key="wrist",
    title="Wrist & hand",
    references=("wu2005",),
    intro=(
        "The hand is described by one generic construction repeated for each metacarpal and phalanx: Y along the "
        "shaft pointing proximally, X volar, Z radial. Every joint of the wrist and fingers uses the same JCS: "
        "flexion about the proximal Z, deviation about the floating axis, axial rotation about the distal Y."
    ),
    segments=("radius", "MC3", "MC2", "PP2", "MP2"),
    joints=("wrist", "mcp2", "pip2"),
    notes=(
        "Thumb: Wu et al. (2005) give dedicated frames for the trapezium and the first metacarpal because the "
        "thumb is rotated relative to the other fingers; they are not drawn here.",
    ),
)

SEGMENTS = (mc3, mc2, pp2, mp2)
JOINTS = (wrist, mcp2, pip2)
