"""Allows running the package directly: python -m voicescribe <audio> [options]"""

import sys

from .cli import main

sys.exit(main())
