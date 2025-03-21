import os
import sys

# Set a default AWS region for tests if not already set.
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-north-1")

# Get the repository root and add it to sys.path.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

print("sys.path:", sys.path)
