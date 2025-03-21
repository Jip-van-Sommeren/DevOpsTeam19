import sys
import os

# Print sys.path for debugging (optional)
print("Before adding src, sys.path:", sys.path)

# Add the project's src directory to sys.path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Print sys.path for debugging (optional)
print("After adding src, sys.path:", sys.path)
