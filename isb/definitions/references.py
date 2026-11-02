from ..model import Reference

REFERENCES = {
    r.key: r
    for r in (
        Reference(
            "wu2002",
            "Wu et al. 2002",
            "Wu G, Siegler S, Allard P, Kirtley C, Leardini A, Rosenbaum D, Whittle M, D'Lima DD, Cristofolini L, "
            "Witte H, Schmid O, Stokes I. ISB recommendation on definitions of joint coordinate system of various "
            "joints for the reporting of human joint motion—part I: ankle, hip, and spine. "
            "Journal of Biomechanics 35(4):543–548, 2002.",
            "10.1016/S0021-9290(01)00222-6",
        ),
        Reference(
            "wu2005",
            "Wu et al. 2005",
            "Wu G, van der Helm FCT, Veeger HEJ, Makhsous M, Van Roy P, Anglin C, Nagels J, Karduna AR, McQuade K, "
            "Wang X, Werner FW, Buchholz B. ISB recommendation on definitions of joint coordinate systems of various "
            "joints for the reporting of human joint motion—Part II: shoulder, elbow, wrist and hand. "
            "Journal of Biomechanics 38(5):981–992, 2005.",
            "10.1016/j.jbiomech.2004.05.042",
        ),
        Reference(
            "grood1983",
            "Grood & Suntay 1983",
            "Grood ES, Suntay WJ. A joint coordinate system for the clinical description of three-dimensional "
            "motions: application to the knee. Journal of Biomechanical Engineering 105(2):136–144, 1983.",
            "10.1115/1.3138397",
        ),
        Reference(
            "wu1995",
            "Wu & Cavanagh 1995",
            "Wu G, Cavanagh PR. ISB recommendations for standardization in the reporting of kinematic data. "
            "Journal of Biomechanics 28(10):1257–1261, 1995.",
            "10.1016/0021-9290(95)00017-C",
        ),
        Reference(
            "senk2006",
            "Šenk & Chèze 2006",
            "Šenk M, Chèze L. Rotation sequence as an important factor in shoulder kinematics. "
            "Clinical Biomechanics 21(Suppl 1):S3–S8, 2006.",
            "10.1016/j.clinbiomech.2005.09.007",
        ),
        Reference(
            "phadke2011",
            "Phadke et al. 2011",
            "Phadke V, Braman JP, LaPrade RF, Ludewig PM. Comparison of glenohumeral motion using different rotation "
            "sequences. Journal of Biomechanics 44(4):700–705, 2011.",
            "10.1016/j.jbiomech.2010.10.042",
        ),
        Reference(
            "spartacus2025",
            "SPARTACUS 2025",
            "SPARTACUS shoulder kinematics dataset and alignment of literature frames to ISB (see the DOI for the "
            "full reference). Journal of Biomechanics, 2025.",
            "10.1016/j.jbiomech.2025.112642",
        ),
    )
}
