#!/usr/bin/env python3
import os
import runpy

BASE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE, "scripts", "tests", "test_nvidia.py")
runpy.run_path(TARGET, run_name="__main__")
