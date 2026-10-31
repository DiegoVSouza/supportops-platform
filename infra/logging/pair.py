#!/usr/bin/env python3
"""Run a worker and an API in one machine: `pair.py <worker...> :: <api...>`.

Fly Proxy can only wake a machine that receives traffic, so a worker shares the
API machine. If either process ends, the other is stopped and the machine restarts.
"""
import signal
import subprocess
import sys
import time


def main():
    arguments = sys.argv[1:]
    if arguments.count('::') != 1 or arguments[0] == '::' or arguments[-1] == '::':
        print('usage: pair.py <worker...> :: <api...>', file=sys.stderr)
        return 2
    split = arguments.index('::')
    processes = [subprocess.Popen(arguments[:split]), subprocess.Popen(arguments[split + 1:])]
    stopping = []

    def stop(signum, _frame):
        stopping.append(signum)
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while all(process.poll() is None for process in processes):
        time.sleep(0.2)
    stop(signal.SIGTERM, None)
    deadline = time.monotonic() + 20
    for process in processes:
        try:
            process.wait(max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
    failed = [process.returncode for process in processes if process.returncode not in (0, -signal.SIGTERM)]
    return failed[0] if failed else 0


if __name__ == '__main__':
    sys.exit(main())
