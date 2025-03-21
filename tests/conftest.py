import os
import sys

# Get the absolute path to the repository root.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print("Repository root:", repo_root)

# Insert the repository root into sys.path if it's not already there.
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

print("Updated sys.path:", sys.path)
