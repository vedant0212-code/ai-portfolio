import unittest

from projects.stayshield import eval as ev
from projects.stayshield import service


class Test(unittest.TestCase):
    def test_smoke(self):
        out = service.draft_claim({"description": "pipe burst", "photos": 1, "items": [{"item": "carpet"}]})
        self.assertEqual(out["status"], "needs_human_review")
        self.assertEqual(out["items"][0]["clause"]["id"], "2.1")

    def test_bundled_eval_runs(self):
        r = ev.run_bundled()
        self.assertEqual(r["project"], "stayshield")
        self.assertTrue(r["metrics"])


if __name__ == "__main__":
    unittest.main()
