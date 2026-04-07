"""Install git pre-push hook (cross-platform: Windows / macOS / Linux)."""

import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_SRC = os.path.join(REPO_ROOT, "hooks", "pre-push")
HOOK_DST_DIR = os.path.join(REPO_ROOT, ".git", "hooks")
HOOK_DST = os.path.join(HOOK_DST_DIR, "pre-push")

if not os.path.isdir(os.path.join(REPO_ROOT, ".git")):
    print("⚠ .git not found, skipping hook install")
    sys.exit(0)

if not os.path.isfile(HOOK_SRC):
    print(f"⚠ {HOOK_SRC} not found, skipping")
    sys.exit(0)

os.makedirs(HOOK_DST_DIR, exist_ok=True)
shutil.copy(HOOK_SRC, HOOK_DST)

# Make executable on Unix (no-op on Windows)
if os.name != "nt":
    os.chmod(HOOK_DST, 0o755)

print("✓ pre-push hook installed")
