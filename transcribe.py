#!/usr/bin/env python3
"""voicescribe command-line entry point: python transcribe.py <audio> [options]"""

import sys

from voicescribe.cli import main

if __name__ == "__main__":
    sys.exit(main())
