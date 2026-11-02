from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, mid, sub, unit

TIBIA_LANDMARKS = ("MM", "LM", "MC", "LC", "TT", "HF")
TIBIA_LINKS = (("MM", "MC"), ("MC", "LC"), ("LC", "LM"), ("LM", "HF"), ("MC", "TT"), ("TT", "LC"), ("MM", "LM"))

tibia_fibula = SegmentCS(
    key="tibia_fibula",
    name="Tibia/fibula",
    region="ankle",
    reference="wu2002",
    section="Ankle joint complex, tibia/fibula coordinate system (XYZ)",
    axes_text={
        "o": "IM, the inter-malleolar point midway between MM and LM.",
        "Z": "Line connecting MM and LM, pointing to the right.",
        "X": "Line perpendicular to the torsional plane of the tibia/fibula (the plane containing IC, MM and LM), "
        "pointing anteriorly.",
        "Y": "Common line perpendicular to X and Z, pointing cranially.",
    },
    steps=(
        Step("IM", mid("MM", "LM"), "Inter-malleolar point, midway between the malleoli.", kind="point"),
        Step("IC", mid("MC", "LC"), "Inter-condylar point, midway between the tibial condyles.", kind="point"),
        Step("o", "IM", "The origin is IM.", kind="origin"),
        Step("Z", unit(sub("LM", "MM")), "Z joins the malleoli; for the right leg LM is lateral, so Z points right."),
        Step(
            "n",
            cross(sub("IC", "MM"), sub("LM", "MM")),
            "Normal of the torsional plane (IC, MM, LM). The order of the cross product makes it point anteriorly.",
            anchor="IM",
        ),
        Step("X", unit("n"), "X is the unit normal of the torsional plane."),
        Step("Y", cross("Z", "X"), "Y completes the right-handed triad and points cranially (along the shank)."),
    ),
    landmarks=TIBIA_LANDMARKS,
    meshes=("tibia", "fibula"),
    links=TIBIA_LINKS,
    planes=(("IC", "MM", "LM"),),
    option_group="tibia",
    option_label="Tibia/fibula (torsional plane)",
    notes=(
        "Because Z follows the malleolar axis, this frame includes tibial torsion: at the ankle it is rotated "
        "externally relative to a knee-based tibia frame.",
        "Y is not exactly the shank long axis IC→IM: it is orthogonal to Z inside the torsional plane.",
    ),
    needs_check=("Landmarks defining the torsional plane (IC, MM, LM).",),
)

tibia = SegmentCS(
    key="tibia",
    name="Tibia",
    region="ankle",
    reference="wu2002",
    section="Ankle joint complex, tibia coordinate system (frontal-plane variant)",
    axes_text={
        "o": "IM.",
        "Y": "Line connecting IM and IC, pointing cranially (tibial long axis).",
        "X": "Line perpendicular to the frontal plane of the tibia (the plane containing IM, MC and LC), "
        "pointing anteriorly.",
        "Z": "Common line perpendicular to X and Y, pointing to the right.",
    },
    steps=(
        Step("IM", mid("MM", "LM"), "Inter-malleolar point.", kind="point"),
        Step("IC", mid("MC", "LC"), "Inter-condylar point.", kind="point"),
        Step("o", "IM", "The origin is IM.", kind="origin"),
        Step("Y", unit(sub("IC", "IM")), "Y is the tibial long axis, from IM up to IC."),
        Step(
            "n",
            cross(sub("MC", "IM"), sub("LC", "IM")),
            "Normal of the frontal plane (IM, MC, LC), pointing anteriorly.",
            anchor="IM",
        ),
        Step("X", unit("n"), "X is the unit normal of the frontal plane."),
        Step("Z", cross("X", "Y"), "Z completes the triad, pointing to the right."),
    ),
    landmarks=TIBIA_LANDMARKS,
    meshes=("tibia", "fibula"),
    links=TIBIA_LINKS,
    planes=(("IM", "MC", "LC"),),
    option_group="tibia",
    option_label="Tibia (frontal plane)",
    notes=(
        "Its Z axis follows the tibial condyles rather than the malleoli, so it does not include tibial torsion. "
        "It is the tibia frame used for the knee joint on this site.",
    ),
    needs_check=("Name and origin of this tibia-only system in Wu et al. 2002 (IM assumed).",),
)


def _neutral_copy(key: str, name: str, landmarks, links, section: str, what: str, meshes) -> SegmentCS:
    return SegmentCS(
        key=key,
        name=name,
        region="ankle",
        reference="wu2002",
        section=section,
        axes_text={
            "o": "Coincident with the tibia/fibula origin (IM) in the neutral configuration.",
            "X": "Coincident with the tibia/fibula X axis in the neutral configuration.",
            "Y": "Coincident with the tibia/fibula Y axis in the neutral configuration.",
            "Z": "Coincident with the tibia/fibula Z axis in the neutral configuration.",
        },
        steps=(
            Step("o", "tibia_fibula.o", "Copy the tibia/fibula origin in the neutral posture.", kind="origin"),
            Step("X", "tibia_fibula.X", "Copy the tibia/fibula X axis."),
            Step("Y", "tibia_fibula.Y", "Copy the tibia/fibula Y axis."),
            Step("Z", "tibia_fibula.Z", f"Copy the tibia/fibula Z axis. The frame is then fixed to the {what}."),
        ),
        landmarks=landmarks,
        links=links,
        meshes=meshes,
        notes=(
            f"The {what} frame has no landmark-based definition: it is defined by the tibia/fibula frame in the "
            "neutral configuration and then moves rigidly with the bone (e.g. tracked with a marker cluster).",
            "Consequence: all ankle JCS angles are zero in the neutral configuration by construction.",
        ),
    )


calcaneus = _neutral_copy(
    "calcaneus",
    "Calcaneus",
    ("CAL", "MH1", "MH5"),
    (("CAL", "MH1"), ("CAL", "MH5"), ("MH1", "MH5")),
    "Ankle joint complex, calcaneus coordinate system (xyz)",
    "calcaneus",
    ("foot",),
)
talus = _neutral_copy(
    "talus",
    "Talus",
    ("TAH",),
    (),
    "Talocrural and subtalar joints, talus coordinate system",
    "talus",
    ("talus",),
)

ANKLE_ANGLES = (
    AngleDef("Dorsiflexion / plantarflexion", "dorsiflexion", "plantarflexion", (-60, 40)),
    AngleDef("Inversion / eversion", "inversion", "eversion", (-40, 40)),
    AngleDef("Internal / external rotation", "internal rotation", "external rotation", (-50, 50)),
)
TRANSLATIONS = (
    "Translations of the distal origin relative to the proximal origin are expressed along e1 (medial-lateral "
    "shift), e2 (anterior-posterior drawer) and e3 (compression-distraction)."
)

ankle_complex = JointCS(
    key="ankle_complex",
    name="Ankle joint complex",
    region="ankle",
    reference="wu2002",
    section="Ankle joint complex JCS",
    parent="tibia_fibula",
    child="calcaneus",
    sequence="ZXY",
    angles=ANKLE_ANGLES,
    axes_text={
        "e1": "Z axis of the tibia/fibula (fixed in the tibia/fibula).",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the calcaneus (fixed in the calcaneus).",
    },
    translations=TRANSLATIONS,
    notes=(
        "Combined motion of the talocrural and subtalar joints: the calcaneus relative to the tibia/fibula.",
        "Inversion/eversion here is a rotation about the floating axis; clinical 'inversion' often also "
        "includes adduction and supination components.",
    ),
    needs_check=("Exact naming of the translations.",),
)

talocrural = JointCS(
    key="talocrural",
    name="Talocrural joint",
    region="ankle",
    reference="wu2002",
    section="Talocrural joint JCS",
    parent="tibia_fibula",
    child="talus",
    sequence="ZXY",
    angles=ANKLE_ANGLES,
    axes_text={
        "e1": "Z axis of the tibia/fibula.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the talus.",
    },
    translations=TRANSLATIONS,
    notes=("Same structure as the ankle joint complex, with the talus as the distal segment.",),
    needs_check=("Angle names for the talocrural joint.",),
)

subtalar = JointCS(
    key="subtalar",
    name="Subtalar joint",
    region="ankle",
    reference="wu2002",
    section="Subtalar joint JCS",
    parent="talus",
    child="calcaneus",
    sequence="ZXY",
    angles=ANKLE_ANGLES,
    axes_text={
        "e1": "Z axis of the talus.",
        "e2": "Floating axis, the common perpendicular of e1 and e3.",
        "e3": "Y axis of the calcaneus.",
    },
    translations=TRANSLATIONS,
    notes=("Same structure as the ankle joint complex, with the talus as the proximal segment.",),
    needs_check=("Angle names for the subtalar joint.",),
)

REGION = Region(
    key="ankle",
    title="Ankle & foot",
    references=("wu2002",),
    intro=(
        "Wu et al. (2002) define the tibia/fibula frame from the malleoli and a torsional plane, and let the "
        "calcaneus (and talus) frames coincide with it in the neutral configuration. The JCS follows Grood & "
        "Suntay: e1 fixed in the tibia/fibula, e3 fixed in the foot bone, e2 floating."
    ),
    segments=("tibia_fibula", "tibia", "calcaneus", "talus"),
    joints=("ankle_complex", "talocrural", "subtalar"),
    notes=(
        "Neutral configuration: the foot is in its neutral standing posture (plantar surface horizontal, "
        "second metatarsal aligned with the sagittal plane), where the calcaneus frame is defined.",
    ),
)

SEGMENTS = (tibia_fibula, tibia, calcaneus, talus)
JOINTS = (ankle_complex, talocrural, subtalar)
