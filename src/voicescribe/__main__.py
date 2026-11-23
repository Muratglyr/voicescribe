"""Entry point for ``python -m voicescribe``."""

import sys

from .cli import main

sys.exit(main())
