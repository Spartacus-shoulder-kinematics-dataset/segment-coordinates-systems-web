from ..model import AngleDef, JointCS, Region, SegmentCS, Step, cross, mid, sub, unit

thorax = SegmentCS(
    key="thorax",
    name="Thorax",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, thorax coordinate system",
    axes_text={
        "o": "IJ, the incisura jugularis.",
        "Y": "Line connecting the midpoint between PX and T8 and the midpoint between IJ and C7, pointing upward.",
        "Z": "Line perpendicular to the plane formed by IJ, C7 and the midpoint between PX and T8, pointing to "
        "the right.",
        "X": "Common line perpendicular to Z and Y, pointing forward.",
    },
    steps=(
        Step("o", "IJ", "The origin is IJ.", kind="origin"),
        Step("m1", mid("IJ", "C7"), "Midpoint between IJ and C7.", kind="point"),
        Step("m2", mid("PX", "T8"), "Midpoint between PX and T8.", kind="point"),
        Step("Y", unit(sub("m1", "m2")), "Y goes from the lower midpoint up to the upper midpoint."),
        Step(
            "n",
            cross(sub("m2", "C7"), sub("IJ", "C7")),
            "Normal of the sagittal plane through IJ, C7 and the lower midpoint; this order makes it point right.",
            anchor="IJ",
        ),
        Step("Z", unit("n"), "Z is the unit normal."),
        Step("X", cross("Y", "Z"), "X completes the triad, pointing forward."),
    ),
    landmarks=("IJ", "PX", "C7", "T8"),
    meshes=("thorax",),
    view=(0.5, 0.3, 1.0),
    links=(("IJ", "PX"), ("C7", "T8"), ("IJ", "C7"), ("PX", "T8")),
    planes=(("IJ", "C7", "m2"),),
    notes=(
        "Y is defined by two midpoints, so it is independent of the relative depth of the sternum and the spine.",
        "The same thorax frame is the parent of the SC, ST and thoracohumeral joints.",
    ),
)

clavicle = SegmentCS(
    key="clavicle",
    name="Clavicle",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, clavicle coordinate system",
    axes_text={
        "o": "SC, the most ventral point on the sternoclavicular joint.",
        "Z": "Line connecting SC and AC, pointing to AC.",
        "X": "Line perpendicular to Z and Y of the thorax, pointing forward.",
        "Y": "Common line perpendicular to X and Z, pointing upward.",
    },
    steps=(
        Step("o", "SC", "The origin is SC.", kind="origin"),
        Step("Z", unit(sub("AC", "SC")), "Z follows the clavicle from SC to AC (laterally)."),
        Step("Yt", "thorax.Y", "Borrow the thorax Y axis: the clavicle has no third landmark.", anchor="SC"),
        Step("X", unit(cross("Yt", "Z")), "X is perpendicular to the clavicle and to the thorax Y, pointing forward."),
        Step("Y", cross("Z", "X"), "Y completes the triad, pointing upward."),
    ),
    landmarks=("SC", "AC"),
    meshes=("clavicle",),
    view=(0.7, 1.0, 0.6),
    links=(("SC", "AC"),),
    notes=(
        "With only two landmarks, the rotation of the clavicle about its long axis cannot be measured from the "
        "skin; X is fixed by the thorax, so clavicular axial rotation is usually estimated or assumed.",
    ),
)

scapula = SegmentCS(
    key="scapula",
    name="Scapula",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, scapula coordinate system",
    axes_text={
        "o": "AA, the angulus acromialis.",
        "Z": "Line connecting TS and AA, pointing to AA.",
        "X": "Line perpendicular to the plane formed by AI, AA and TS, pointing forward.",
        "Y": "Common line perpendicular to X and Z, pointing upward.",
    },
    steps=(
        Step("o", "AA", "The origin is AA.", kind="origin"),
        Step("Z", unit(sub("AA", "TS")), "Z follows the scapular spine from TS to AA."),
        Step(
            "n",
            cross(sub("TS", "AI"), sub("AA", "AI")),
            "Normal of the scapular plane (AI, AA, TS); this order makes it point forward.",
            anchor="AA",
        ),
        Step("X", unit("n"), "X is the unit normal of the scapular plane."),
        Step("Y", cross("Z", "X"), "Y completes the triad, pointing upward."),
    ),
    landmarks=("AA", "TS", "AI", "AC", "GC"),
    meshes=("scapula",),
    view=(-1.0, 0.35, 0.7),
    links=(("AA", "TS"), ("TS", "AI"), ("AI", "GC"), ("GC", "AC"), ("AC", "AA")),
    planes=(("AA", "TS", "AI"),),
    notes=(
        "Earlier conventions used the acromioclavicular joint or the glenoid as origin; the SPARTACUS project "
        "(J Biomech 2025) shows how such origins and axes are converted to the ISB scapula.",
        "Because X is normal to the scapular plane, the scapula frame is rotated ~30–40° from the thorax frame in "
        "the anatomical position (scapular protraction).",
    ),
)

humerus = SegmentCS(
    key="humerus",
    name="Humerus",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, humerus coordinate system (option 1)",
    axes_text={
        "o": "GH, the glenohumeral rotation centre.",
        "Y": "Line connecting GH and the midpoint of EL and EM, pointing to GH.",
        "X": "Line perpendicular to the plane formed by EL, EM and GH, pointing forward.",
        "Z": "Common line perpendicular to Y and X, pointing to the right.",
    },
    steps=(
        Step("o", "GH", "The origin is GH.", kind="origin"),
        Step("mE", mid("EL", "EM"), "Midpoint of the epicondyles.", kind="point"),
        Step("Y", unit(sub("GH", "mE")), "Y goes from the elbow up to GH."),
        Step(
            "n",
            cross(sub("EL", "GH"), sub("EM", "GH")),
            "Normal of the plane (EL, EM, GH); this order makes it point forward.",
            anchor="GH",
        ),
        Step("X", unit("n"), "X is the unit normal."),
        Step("Z", cross("X", "Y"), "Z completes the triad, pointing to the right."),
    ),
    landmarks=("GH", "EL", "EM"),
    meshes=("humerus",),
    links=(("GH", "EL"), ("GH", "EM"), ("EL", "EM")),
    planes=(("GH", "EL", "EM"),),
    option_group="humerus",
    option_label="Option 1 (epicondyles)",
    notes=(
        "Option 1 depends only on humeral landmarks, but the epicondyles are close together, so small landmark "
        "errors produce large errors in humeral axial rotation.",
    ),
)

humerus_opt2 = SegmentCS(
    key="humerus_opt2",
    name="Humerus",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, humerus coordinate system (option 2)",
    axes_text={
        "o": "GH.",
        "Y": "Line connecting GH and the midpoint of EL and EM, pointing to GH.",
        "Z": "Line perpendicular to Y and to the forearm long axis Yf (elbow flexed 90°), pointing to the right.",
        "X": "Common line perpendicular to Y and Z, pointing forward.",
    },
    steps=(
        Step("o", "GH", "The origin is GH.", kind="origin"),
        Step("mE", mid("EL", "EM"), "Midpoint of the epicondyles.", kind="point"),
        Step("Y", unit(sub("GH", "mE")), "Y goes from the elbow up to GH."),
        Step(
            "Yf",
            unit(sub("mE", "US90")),
            "Forearm long axis with the elbow flexed 90°: from the ulnar styloid back to the elbow.",
        ),
        Step("Z", unit(cross("Y", "Yf")), "Z is perpendicular to the humerus and to the flexed forearm."),
        Step("X", cross("Y", "Z"), "X completes the triad, pointing forward."),
    ),
    landmarks=("GH", "EL", "EM", "US90"),
    meshes=("humerus",),
    view=(0.6, 0.5, 1.0),
    links=(("GH", "EL"), ("GH", "EM"), ("EL", "EM"), ("EM", "US90"), ("EL", "US90")),
    option_group="humerus",
    option_label="Option 2 (forearm at 90°)",
    notes=(
        "Option 2 uses the flexed forearm as a long lever arm, which makes humeral axial rotation much less "
        "sensitive to landmark errors; it requires a calibration posture with the elbow flexed 90°.",
    ),
)

SCAP_ANGLES = (
    AngleDef("Protraction / retraction", "protraction", "retraction", (-60, 80)),
    AngleDef("Medial / lateral rotation", "medial (downward) rotation", "lateral (upward) rotation", (-70, 40)),
    AngleDef("Posterior / anterior tilt", "posterior tilt", "anterior tilt", (-40, 40)),
)

HUMERAL_ANGLES = (
    AngleDef("Plane of elevation", "towards forward flexion", "towards extension", (-180, 180),
             "0° is abduction in the frontal plane, 90° is forward flexion in the sagittal plane."),
    AngleDef("Elevation", "depression (not physiological)", "elevation", (-180, 0),
             "Elevation is a negative rotation about the rotated X axis."),
    AngleDef("Axial rotation", "internal rotation", "external rotation", (-120, 120)),
)

sternoclavicular = JointCS(
    key="sc",
    name="Sternoclavicular joint",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, SC joint JCS",
    parent="thorax",
    child="clavicle",
    sequence="YXZ",
    view=(0.7, 1.0, 0.6),
    angles=(
        AngleDef("Protraction / retraction", "protraction", "retraction", (-60, 40)),
        AngleDef("Depression / elevation", "depression", "elevation", (-50, 20)),
        AngleDef("Axial rotation", "backward rotation", "forward rotation", (-60, 60)),
    ),
    axes_text={
        "e1": "Y axis of the thorax.",
        "e2": "Floating axis: the X axis after the first rotation, perpendicular to e1 and e3.",
        "e3": "Z axis of the clavicle.",
    },
    translations="Not reported: SC translations are considered negligible.",
    notes=(
        "Axial rotation of the clavicle cannot be measured with skin landmarks (see the clavicle frame).",
        "At rest the clavicle is retracted by ~20° and slightly elevated.",
    ),
)

acromioclavicular = JointCS(
    key="ac",
    name="Acromioclavicular joint",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, AC joint JCS",
    parent="clavicle",
    child="scapula",
    sequence="YXZ",
    pivot="AC",
    view=(-0.9, 0.4, 0.8),
    angles=SCAP_ANGLES,
    axes_text={
        "e1": "Y axis of the clavicle.",
        "e2": "Floating axis, perpendicular to e1 and e3.",
        "e3": "Z axis of the scapula.",
    },
    notes=("The AC angles are large at rest because the clavicle and scapula frames are far from aligned.",),
)

scapulothoracic = JointCS(
    key="st",
    name="Scapulothoracic 'joint'",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, ST JCS",
    parent="thorax",
    child="scapula",
    sequence="YXZ",
    pivot="AC",
    view=(-0.9, 0.4, 0.8),
    angles=SCAP_ANGLES,
    axes_text={
        "e1": "Y axis of the thorax.",
        "e2": "Floating axis, perpendicular to e1 and e3.",
        "e3": "Z axis of the scapula.",
    },
    notes=(
        "Not an anatomical joint: the orientation of the scapula relative to the thorax, which combines SC and AC.",
        "Clinical reports often give upward rotation as positive, i.e. the opposite of the ISB sign here.",
    ),
)

glenohumeral = JointCS(
    key="gh",
    name="Glenohumeral joint",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, GH joint JCS",
    parent="scapula",
    child="humerus",
    sequence="YXY",
    middle_negative=True,
    view=(0.5, 0.3, 1.0),
    angles=HUMERAL_ANGLES,
    axes_text={
        "e1": "Y axis of the scapula.",
        "e2": "Floating axis, perpendicular to e1 and e3.",
        "e3": "Y axis of the humerus.",
    },
    translations="GH translations are small and usually not reported with skin-based methods.",
    notes=(
        "YXY is a proper Euler sequence: when the elevation is 0° (arm along the body) the first and third axes "
        "coincide (gimbal lock), and the plane of elevation and axial rotation cannot be separated.",
        "Alternatives such as XZY (Phadke et al. 2011) or ZXY avoid the lock in low elevation; "
        "Šenk & Chèze (2006) show how strongly the chosen sequence changes the reported angles.",
    ),
)

thoracohumeral = JointCS(
    key="th",
    name="Thoracohumeral (humerus relative to thorax)",
    region="shoulder",
    reference="wu2005",
    section="Shoulder, thoracohumeral JCS",
    parent="thorax",
    child="humerus",
    sequence="YXY",
    middle_negative=True,
    view=(0.5, 0.3, 1.0),
    angles=HUMERAL_ANGLES,
    axes_text={
        "e1": "Y axis of the thorax.",
        "e2": "Floating axis, perpendicular to e1 and e3.",
        "e3": "Y axis of the humerus.",
    },
    notes=(
        "The global description of arm motion: plane of elevation, elevation, axial rotation.",
        "Same YXY gimbal lock as the GH joint, in the arm-at-side posture.",
    ),
)

REGION = Region(
    key="shoulder",
    title="Shoulder",
    references=("wu2005",),
    intro=(
        "Wu et al. (2005) define frames for the thorax, clavicle, scapula and humerus (two options), and the "
        "sternoclavicular, acromioclavicular, scapulothoracic, glenohumeral and thoracohumeral JCS. Unlike the "
        "lower limb, the shoulder uses the YXZ Cardan sequence for the shoulder girdle and the YXY Euler sequence "
        "for the humerus (plane of elevation, elevation, axial rotation)."
    ),
    segments=("thorax", "clavicle", "scapula", "humerus", "humerus_opt2"),
    joints=("sc", "ac", "st", "gh", "th"),
    notes=(
        "The anatomical position is not the zero of the shoulder JCS: at rest the clavicle is retracted, the "
        "scapula protracted and rotated, so the SC, AC and ST angles are far from zero.",
    ),
)

SEGMENTS = (thorax, clavicle, scapula, humerus, humerus_opt2)
JOINTS = (sternoclavicular, acromioclavicular, scapulothoracic, glenohumeral, thoracohumeral)
