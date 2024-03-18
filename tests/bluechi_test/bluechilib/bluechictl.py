# SPDX-License-Identifier: LGPL-2.1-or-later

import copy
import signal
import subprocess
import threading
import time
import tempfile
from typing import List, Pattern, Set, Tuple


class FileFollower:
    def __init__(self, file_name):
        self.pos = 0
        self.file_name = file_name
        self.file_desc = None

    def __enter__(self):
        self.file_desc = open(self.file_name, mode='r')
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if (exception_type):
            print(f"Exception raised: excpetion_type='{exception_type}', "
                  f"exception_value='{exception_value}', exception_traceback: {exception_traceback}")
        if self.file_desc:
            self.file_desc.close()

    def __iter__(self):
        while self.new_lines():
            self.seek()
            line = self.file_desc.read().split('\n')[0]
            yield line

            self.pos += len(line) + 1

    def seek(self):
        self.file_desc.seek(self.pos)

    def new_lines(self):
        self.seek()
        return '\n' in self.file_desc.read()


class BluechiCtlBackgroundRunner:
    def __init__(self, command: List, expected_patterns: Set[Pattern]):
        self.command = command
        self.expected_patterns = copy.copy(expected_patterns)
        self.thread = threading.Thread(target=self.process_events)
        self.failsafe_thread = threading.Thread(target=self.timeout_guard, daemon=True)
        self.all_found = False
        self.finished = False
        self.bluechictl_proc = None

    def process_events(self):
        print("Starting process_events")
        with tempfile.NamedTemporaryFile() as out_file:
            try:
                self.bluechictl_proc = subprocess.Popen(self.command, stdout=out_file, bufsize=1)

                with FileFollower(out_file.name) as bluechictl_out:
                    while self.bluechictl_proc.poll() is None and not self.finished:
                        for line in bluechictl_out:
                            print(f"Evaluating line '{line}'")
                            match = None
                            for pattern in copy.copy(self.expected_patterns):
                                match = pattern.match(line)
                                if match:
                                    print(f"Matched line '{line}'")
                                    self.expected_patterns.remove(pattern)
                                    break
                            if not match:
                                print(f"Ignoring line '{line}'")
                                continue
                            if len(self.expected_patterns) == 0:
                                print("All patterns were matched")
                                self.all_found = True
                                self.finished = True
                                break

                        # Wait for the new output from bluechictl monitor
                        time.sleep(0.5)
            finally:
                print("Finalizing process")
                if self.bluechictl_proc:
                    self.bluechictl_proc.send_signal(signal.SIGINT)
                    self.bluechictl_proc.wait()
                    self.bluechictl_proc = None

    def timeout_guard(self):
        time.sleep(10)
        print(f"Waiting for expected output in {self.command} has timed out")
        self.bluechictl_proc.send_signal(signal.SIGINT)
        self.bluechictl_proc.wait()

    def start(self):
        print("Starting thread...")
        self.thread.start()

    def stop(self):
        self.finished = True
        self.thread.join()

    def found_all_patterns(self):
        return self.all_found


class BluechiCtl:
    def run(self, args: List) -> Tuple[str, str]:
        command = ["bluechictl"] + args
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Executing of command '{process.args}' started")
        return process.communicate()

    def metrics_listen(self) -> Tuple[str, str]:
        return self.run(["metrics", "listen"])

    def metrics_enable(self) -> Tuple[str, str]:
        return self.run(["metrics", "enable"])

    def metrics_disable(self) -> Tuple[str, str]:
        return self.run(["metrics", "disable"])

    def unit_start(self, node, unit) -> Tuple[str, str]:
        return self.run(["start", node, unit])

    def unit_stop(self, node, unit) -> Tuple[str, str]:
        return self.run(["stop", node, unit])
