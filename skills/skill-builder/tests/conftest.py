import sys
from pathlib import Path

# Needed because skill-builder scripts use "from scripts.X import Y"
# which requires the skill-builder root on sys.path.
sys.path.insert(0, str(Path(__file__).parent.parent))
