from ..model import AngleDef, JointCS, Region, mid

knee = JointCS(
    key="knee",
    name="Knee (tibiofemoral) joint",
    region="knee",
    reference="grood1983",
    section="Joint coordinate system for the knee",
    parent="femur",
    child="tibia",
    sequence="ZXY",
    pivot=mid("LFE", "MFE"),
    angles=(
        AngleDef(
            "Flexion / extension",
            "extension",
            "flexion",
            (-150, 15),
            "With Z to the right, knee flexion is a negative rotation about e1. Grood & Suntay (and most reports) "
            "give flexion as a positive number, i.e. flexion = −α.",
        ),
        AngleDef("Adduction (varus) / abduction (valgus)", "adduction (varus)", "abduction (valgus)", (-20, 20)),
        AngleDef("Internal / external tibial rotation", "internal rotation", "external rotation", (-40, 40)),
    ),
    axes_text={
        "e1": "Medial-lateral axis fixed in the femur (here the femoral Z axis of Wu et al. 2002).",
        "e2": "Floating axis, the common perpendicular of e1 and e3 (roughly anterior).",
        "e3": "Long axis of the tibia, fixed in the tibia (here the tibial Y axis).",
    },
    translations=(
        "Grood & Suntay define three clinical translations of the tibial origin relative to the femoral origin: "
        "medial-lateral shift along e1, anterior-posterior drawer along e2, and joint distraction-compression "
        "along e3."
    ),
    notes=(
        "Grood & Suntay designed the JCS so that each rotation and translation has a clinical meaning, and so "
        "that the rotations are sequence-independent when described as rotations about e1, e2 and e3.",
        "The same construction is what ISB adopted for every Wu et al. 2002 joint, which is why this knee page "
        "reuses the femur (hip page) and the frontal-plane tibia (ankle page).",
        "Cross-talk: an error in the orientation of e1 (the flexion axis) leaks flexion into ab/adduction; this "
        "is the main source of spurious varus/valgus in gait analysis.",
    ),
    needs_check=("Wu et al. 2002 did not publish a knee recommendation; the frames used here are an assumption.",),
)

REGION = Region(
    key="knee",
    title="Knee",
    references=("grood1983", "wu2002"),
    intro=(
        "ISB has not published a separate knee recommendation; Wu et al. (2002) build on the joint coordinate "
        "system that Grood & Suntay (1983) introduced for the knee. This page applies it to the femur and tibia "
        "frames defined elsewhere on the site."
    ),
    segments=("femur", "tibia"),
    joints=("knee",),
    status="Referenced by ISB (Grood & Suntay 1983), not a separate ISB recommendation",
)

SEGMENTS = ()
JOINTS = (knee,)
