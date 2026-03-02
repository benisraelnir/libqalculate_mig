"""
Pytest configuration and shared fixtures for qalculate tests.
"""

import sys
import os

# Add the python package to the path so tests can import qalculate
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
