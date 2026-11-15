"""Convenience wrapper for the installed IGNIS CLI."""
import sys
from ignis_ml.cli import main

if __name__ == "__main__":
    raise SystemExit(main(['demo'] + sys.argv[1:]))
