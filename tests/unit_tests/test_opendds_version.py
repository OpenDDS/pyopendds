import unittest

import pyopendds


class TestOpenDdsVersion(unittest.TestCase):

    def test_opendds_version_str(self):
        s = pyopendds.opendds_version_str()
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 0)

    def test_opendds_version_tuple(self):
        t = pyopendds.opendds_version_tuple()
        self.assertIsInstance(t, tuple)
        self.assertEqual(len(t), 3)
        self.assertGreaterEqual(t[0], 3)

    def test_opendds_version_dict(self):
        d = pyopendds.opendds_version_dict()
        self.assertIsInstance(d, dict)
        self.assertIn('major', d)
        self.assertGreaterEqual(d['major'], 3)
        self.assertIn('minor', d)
        self.assertIn('micro', d)
        self.assertIn('metadata', d)
        self.assertIn('is_release', d)
