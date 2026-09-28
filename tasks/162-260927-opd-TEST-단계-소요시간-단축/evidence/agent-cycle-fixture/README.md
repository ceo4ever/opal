# Task 162 TEST cycle fixture

This directory is an isolated TEST procedure fixture. `setup.py` calls the
installed state-tool and test-tool CLIs to create a disposable task, two human
handoffs, and two automatic scenarios. It also initializes a local Git
repository with small executable pytest cases. It never touches the real task
registry, task 161 or task 163, and has no remote.

Run `setup.py` once from this directory. The PM must issue the two human
requests together and start the two human clocks before the TEST executor
starts the automatic scenarios. All CLI outputs and exit codes go in `trace/`.
