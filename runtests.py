'''
To run tests:

$ ~/mp_app_env/bin/python runtests.py
$ ~/mp_app_env/bin/python runtests.py --coverage
'''

import os
import subprocess
import sys

def main(args):
    command = ["-m", "unittest", "tests"]
    if "--coverage" in args:
        coverage = os.path.join(os.path.dirname(sys.executable), "coverage")
        exe = [coverage, "run", "--source", "."]
        after = [coverage, "report", "-m"]
    else:
        exe = [sys.executable]
        after = []

    subprocess.check_call(exe + command)
    if after:
        print ""
        subprocess.check_call(after)

if __name__ == "__main__":
    main(sys.argv)
