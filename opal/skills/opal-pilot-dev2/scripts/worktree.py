#!/usr/bin/env python3
"""Forward worktree operations to the installed OPAL public tools, without fallback."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opal-root', type=Path, default=Path.home() / '.opal')
    parser.add_argument('operation', choices=['create', 'status', 'checkpoint', 'finalize', 'remove',
                                             'launch', 'read', 'recover', 'close'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    family = 'worktree-launcher' if args.operation in ('launch', 'read', 'recover', 'close') else 'worktree-tool'
    command = args.opal_root / 'tools' / family / 'run.sh'
    if not command.is_file():
        print(json.dumps({'ok': False, 'error': 'engine_missing', 'path': str(command)}))
        return 2
    # OPAL owns flags, registry, lease, permissions, and return status.
    return subprocess.run([str(command), args.operation, *args.arguments], check=False).returncode


if __name__ == '__main__':
    sys.exit(main())
