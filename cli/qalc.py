#!/usr/bin/env python3
"""Thin wrapper that delegates to the installed qalculate.cli module."""
import sys
from qalculate.cli import main
sys.exit(main())
