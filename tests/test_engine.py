"""Unit tests for swarm-quorum-consensus-engine."""
import unittest
from swarm_quorum_consensus_engine.engine import SwarmQuorumEngine


class TestSwarmQuorumEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SwarmQuorumEngine(quorum_ratio=0.60)
        self.engine.register_agent("a1", weight=1.0)
        self.engine.register_agent("a2", weight=1.0)
        self.engine.register_agent("a3", weight=2.0)  # total = 4.0

    def test_proposal_and_commit(self):
        prop = self.engine.submit_proposal("p1", "scale_workers", {"replicas": 5}, "a1")
        self.engine.cast_vote("a1", "p1", True)
        self.engine.cast_vote("a3", "p1", True)  # 3.0 / 4.0 = 0.75 >= 0.60
        res = self.engine.evaluate_quorum("p1")
        self.assertEqual(res["status"], "COMMITTED")
        self.assertIn("certificate_hash", res)

    def test_proposal_rejection(self):
        prop = self.engine.submit_proposal("p2", "drop_db", {}, "a2")
        self.engine.cast_vote("a1", "p2", False)
        self.engine.cast_vote("a3", "p2", False)  # 3.0 rejected > 40%
        res = self.engine.evaluate_quorum("p2")
        self.assertEqual(res["status"], "REJECTED")

    def test_unregistered_agent_rejection(self):
        with self.assertRaises(KeyError):
            self.engine.submit_proposal("p3", "run", {}, "rogue_agent")
