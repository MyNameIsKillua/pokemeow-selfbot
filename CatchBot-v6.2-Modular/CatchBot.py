"""CatchBot entry point. Run this file to start the bot."""
import os
import sys

# Ensure this directory is on the import path so subpackages resolve.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from core.entry import main

if __name__ == "__main__":
    main()
