import sys
from pathlib import Path

# Add project root and CraftLab-ctl to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
ctl_src = repo_root / "CraftLab-ctl" / "src"

for p in (str(repo_root), str(ctl_src)):
    if p not in sys.path:
        sys.path.insert(0, p)
