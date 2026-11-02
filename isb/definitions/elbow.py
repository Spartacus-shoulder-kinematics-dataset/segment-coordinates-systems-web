from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, mid, sub, unit

forearm = SegmentCS(
    key="forearm",
    name="Forearm",
    region="elbow",
    reference="wu2005",
    section="Elbow, forearm coordinate system",
    axes_text={
        "o": "US, the ulnar styloid.",
        "Y": "Line connecting US and the midpoint between EL and EM, pointing proximally.",
        "X": "Line perpendicular to the plane through US, RS and the midpoint between EL and EM, pointing forward.",
        "Z": "Common line perpendicular to X and Y, pointing to the right.",
    },
    steps=(
        Step("o", "US", "The origin is US.", kind="origin"),
        Step("mE", mid("EL", "EM"), "Midpoint of the epicondyles.", kind="point"),
        Step("Y", unit(sub("mE", "US")), "Y goes from US up to the elbow."),
        Step(
            "n",
            cross(sub("mE", "US"), sub("RS", "US")),
            "Normal of the plane (US, RS, elbow midpoint); this order makes it point forward in the anatomical "
            "position (forearm supinated).",
            anchor="US",
        ),
        Step("X", unit("n"), "X is the unit normal."),
        Step("Z", cross("X", "Y"), "Z completes the triad, pointing to the right."),
    ),
    landmarks=("US", "RS", "EL", "EM"),
    meshes=("ulna", "radius"),
    links=(("EM", "US"), ("EL", "RS"), ("US", "RS"), ("EL", "EM")),
    planes=(("US", "RS", "mE"),),
    notes=(
        "This frame rotates with pronation: in the anatomical position (supination) X points forward, in "
        "full pronation it points backward.",
    ),
)

ulna = SegmentCS(
    key="ulna",
    name="Ulna",
    region="elbow",
    reference="wu2005",
    section="Elbow, ulna coordinate system",
    axes_text={
        "o": "US.",
        "Y": "Line connecting US and the midpoint between EL and EM, pointing proximally.",
        "X": "Line perpendicular to the plane through US, EL and EM, pointing forward.",
        "Z": "Common line perpendicular to X and Y, pointing to the right.",
    },
    steps=(
        Step("o", "US", "The origin is US.", kind="origin"),
        Step("mE", mid("EL", "EM"), "Midpoint of the epicondyles.", kind="point"),
        Step("Y", unit(sub("mE", "US")), "Y goes from US up to the elbow."),
        Step(
            "n",
            cross(sub("EM", "US"), sub("EL", "US")),
            "Normal of the plane (US, EL, EM), pointing forward.",
            anchor="US",
        ),
        Step("X", unit("n"), "X is the unit normal."),
        Step("Z", cross("X", "Y"), "Z completes the triad, pointing to the right."),
    ),
    landmarks=("US", "EL", "EM"),
    meshes=("ulna",),
    links=(("EM", "US"), ("EL", "US"), ("EL", "EM")),
    planes=(("US", "EL", "EM"),),
    notes=("The ulna frame uses the humeral epicondyles, so it assumes the elbow is in a reference posture.",),
    needs_check=("Exact landmarks of the ulna frame (US, EL, EM assumed).",),
)

radius = SegmentCS(
    key="radius",
    name="Radius",
    region="elbow",
    reference="wu2005",
    section="Elbow, radius coordinate system",
    axes_text={
        "o": "RS, the radial styloid.",
        "Y": "Line connecting RS and EL, pointing proximally.",
        "X": "Line perpendicular to the plane through US, RS and EL, pointing forward.",
        "Z": "Common line perpendicular to X and Y, pointing to the right.",
    },
    steps=(
        Step("o", "RS", "The origin is RS.", kind="origin"),
        Step("Y", unit(sub("EL", "RS")), "Y goes from RS up to EL (the radius lies laterally)."),
        Step(
            "n",
            cross(sub("US", "RS"), sub("EL", "RS")),
            "Normal of the plane (US, RS, EL), pointing forward.",
            anchor="RS",
        ),
        Step("X", unit("n"), "X is the unit normal."),
        Step("Z", cross("X", "Y"), "Z completes the triad, pointing to the right."),
    ),
    landmarks=("RS", "US", "EL"),
    meshes=("radius",),
    links=(("EL", "RS"), ("US", "RS")),
    planes=(("US", "RS", "EL"),),
    needs_check=("Exact landmarks of the radius frame (RS, US, EL assumed).",),
)

elbow = JointCS(
    key="elbow",
    name="Elbow (humerus–forearm)",
    region="elbow",
    reference="wu2005",
    section="Elbow JCS",
    parent="humerus",
    child="forearm",
    sequence="ZXY",
    pivot=mid("EL", "EM"),
    angles=(
        AngleDef("Flexion / hyperextension", "flexion", "hyperextension", (-10, 150)),
        AngleDef("Carrying angle (adduction / abduction)", "adduction (varus)", "abduction (valgus)", (-30, 20),
                 "The physiological carrying angle is a valgus (negative) angle."),
        AngleDef("Axial rotation (pronation / supination)", "pronation", "supination", (-90, 90)),
    ),
    axes_text={
        "e1": "Z axis of the humerus.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the forearm.",
    },
    translations="Elbow translations are not usually reported.",
    notes=(
        "The forearm frame contains pronation/supination, so the third angle of this JCS mixes humeroulnar and "
        "radioulnar motion.",
    ),
    needs_check=("Whether Wu et al. 2005 use the forearm or the ulna as the distal segment of this JCS.",),
)

radioulnar = JointCS(
    key="radioulnar",
    name="Radioulnar joint",
    region="elbow",
    reference="wu2005",
    section="Radioulnar JCS",
    parent="ulna",
    child="radius",
    sequence="ZXY",
    pivot="EL",
    angles=(
        AngleDef("Flexion / extension (radius about ulna)", "flexion", "extension", (-20, 20)),
        AngleDef("Adduction / abduction", "adduction", "abduction", (-20, 20)),
        AngleDef("Pronation / supination", "pronation", "supination", (-90, 90)),
    ),
    axes_text={
        "e1": "Z axis of the ulna.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the radius.",
    },
    notes=("Only the third angle (pronation/supination) is physiologically significant.",),
    needs_check=("Axes of the radioulnar JCS (e1 = ulna Z, e3 = radius Y assumed).",),
)

REGION = Region(
    key="elbow",
    title="Elbow & forearm",
    references=("wu2005",),
    intro=(
        "The forearm, ulna and radius frames all use the styloids and the humeral epicondyles. The elbow JCS "
        "describes the forearm relative to the humerus with flexion about the humeral Z axis, the carrying angle "
        "about the floating axis, and axial rotation about the forearm Y axis."
    ),
    segments=("humerus", "forearm", "ulna", "radius"),
    joints=("elbow", "radioulnar"),
)

SEGMENTS = (forearm, ulna, radius)
JOINTS = (elbow, radioulnar)
