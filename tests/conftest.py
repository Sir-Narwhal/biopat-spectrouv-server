"""
conftest.py

Adds app/ to sys.path so tests can import from parselibrary without
needing to install the package.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
