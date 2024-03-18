# SPDX-License-Identifier: LGPL-2.1-or-later

import re
import time
import unittest

from bluechi_test.bluechilib.bluechictl import BluechiCtlBackgroundRunner, BluechiCtl

node_foo_name = "node-foo"
service_simple = "simple.service"


class TestBluechictlMetrics(unittest.TestCase):

    def setUp(self) -> None:
        signal_agent_metrics_start_pat = re.compile(r"^.*Agent systemd StartUnit job.*")
        signal_agent_metrics_stop_pat = re.compile(r"^.*Agent systemd StopUnit job.*")
        signal_controller_metrics_pat = re.compile(r"^.*BlueChi job gross measured time.*")
        expected_patterns = {signal_agent_metrics_start_pat,
                             signal_agent_metrics_stop_pat,
                             signal_controller_metrics_pat}
        command = ["/usr/bin/bluechictl", "metrics", "listen"]
        self.bgrunner = BluechiCtlBackgroundRunner(command, expected_patterns)
        self.bluechictl = BluechiCtl()

    def test_bluechictl_metrics(self):
        self.bluechictl.metrics_enable()
        self.bgrunner.start()
        time.sleep(0.5)
        self.bluechictl.unit_start(node_foo_name, service_simple)
        time.sleep(0.5)
        self.bluechictl.unit_stop(node_foo_name, service_simple)
        time.sleep(0.5)
        self.bgrunner.stop()
        assert self.bgrunner.found_all_patterns()


if __name__ == "__main__":
    unittest.main()
