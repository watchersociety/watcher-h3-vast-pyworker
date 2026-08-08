import os
import unittest
from unittest.mock import patch

from worker import video_workload


class VideoWorkloadTests(unittest.TestCase):
    def test_default_three_second_request_is_twelve_thousand_units(self):
        self.assertEqual(video_workload({
            "width": 1344,
            "height": 768,
            "durationSeconds": 3,
        }), 12000.0)

    def test_environment_override_changes_output_second_calibration(self):
        with patch.dict(os.environ, {"VAST_H3_LOAD_UNITS_PER_OUTPUT_SECOND": "5000"}):
            self.assertEqual(video_workload({
                "width": 1344,
                "height": 768,
                "durationSeconds": 10,
            }), 50000.0)


if __name__ == "__main__":
    unittest.main()
