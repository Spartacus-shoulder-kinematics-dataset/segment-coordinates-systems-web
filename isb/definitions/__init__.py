"""Registry of every region, segment and joint shown on the site."""

from . import ankle, elbow, hip, knee, shoulder, spine, wrist_hand
from .references import REFERENCES

_MODULES = (ankle, hip, knee, spine, shoulder, elbow, wrist_hand)

REGIONS = {m.REGION.key: m.REGION for m in _MODULES}
SEGMENTS = {s.key: s for m in _MODULES for s in m.SEGMENTS}
JOINTS = {j.key: j for m in _MODULES for j in m.JOINTS}

__all__ = ["REFERENCES", "REGIONS", "SEGMENTS", "JOINTS"]
