"""Make ``agentops_local`` importable when running tests from any cwd."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
