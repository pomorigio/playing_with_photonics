# utils/meep_utils/digital_twins/__init__.py

# 1. Import your components here
from .mmi import MMI1x2Twin, MMI2x2Twin
from .dc import DirectionalCouplerTwin  # Assuming you have this in dc.py
# from .ring import RingResonatorTwin   # Future components...

# 2. (Optional but recommended) Define __all__
# This restricts what gets exported when someone does "from digital_twins import *"
__all__ = [
    "MMI1x2Twin",
    "MMI2x2Twin",
    "DirectionalCouplerTwin",
]