"""Core Swarm Quorum Consensus Engine implementation."""
import time
import hashlib
from typing import Dict, List, Optional, Any


class Proposal:
    def __init__(self, proposal_id: str, action: str, payload: Dict[str, Any], proposer_id: str):
        self.proposal_id = proposal_id
        self.action = action
        self.payload = payload
        self.proposer_id = proposer_id
        self.created_at = time.time()
        self.hash = hashlib.sha256(f"{proposal_id}:{action}:{proposer_id}:{self.created_at}".encode()).hexdigest()[:16]


class Vote:
    def __init__(self, agent_id: str, proposal_id: str, approve: bool, weight: float = 1.0, reason: str = ""):
        self.agent_id = agent_id
        self.proposal_id = proposal_id
        self.approve = approve
        self.weight = weight
        self.reason = reason
        self.timestamp = time.time()


class SwarmQuorumEngine:
    def __init__(self, quorum_ratio: float = 0.67):
        self.quorum_ratio = quorum_ratio
        self.registered_agents: Dict[str, float] = {}  # agent_id -> weight
        self.proposals: Dict[str, Proposal] = {}
        self.votes: Dict[str, Dict[str, Vote]] = {}  # proposal_id -> {agent_id: Vote}
        self.committed_proposals: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent_id: str, weight: float = 1.0):
        self.registered_agents[agent_id] = max(0.1, weight)

    def total_swarm_weight(self) -> float:
        return sum(self.registered_agents.values())

    def submit_proposal(self, proposal_id: str, action: str, payload: Dict[str, Any], proposer_id: str) -> Proposal:
        if proposer_id not in self.registered_agents:
            raise KeyError(f"Proposer {proposer_id} is not a registered swarm member")
        prop = Proposal(proposal_id, action, payload, proposer_id)
        self.proposals[proposal_id] = prop
        self.votes[proposal_id] = {}
        return prop

    def cast_vote(self, agent_id: str, proposal_id: str, approve: bool, reason: str = "") -> Vote:
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal {proposal_id} does not exist")
        if agent_id not in self.registered_agents:
            raise KeyError(f"Agent {agent_id} is not registered")
        if proposal_id in self.committed_proposals:
            raise ValueError(f"Proposal {proposal_id} is already finalized")

        weight = self.registered_agents[agent_id]
        vote = Vote(agent_id, proposal_id, approve, weight, reason)
        self.votes[proposal_id][agent_id] = vote
        return vote

    def evaluate_quorum(self, proposal_id: str) -> Dict[str, Any]:
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal {proposal_id} not found")

        total_weight = self.total_swarm_weight()
        if total_weight == 0:
            return {"status": "PENDING", "ratio": 0.0}

        prop_votes = self.votes.get(proposal_id, {})
        approved_weight = sum(v.weight for v in prop_votes.values() if v.approve)
        rejected_weight = sum(v.weight for v in prop_votes.values() if not v.approve)

        current_approval_ratio = approved_weight / total_weight
        current_rejection_ratio = rejected_weight / total_weight

        if current_approval_ratio >= self.quorum_ratio:
            cert = {
                "proposal_id": proposal_id,
                "status": "COMMITTED",
                "approved_weight": approved_weight,
                "total_weight": total_weight,
                "approval_ratio": current_approval_ratio,
                "certificate_hash": hashlib.sha256(f"{proposal_id}:COMMITTED:{approved_weight}".encode()).hexdigest()[:16]
            }
            self.committed_proposals[proposal_id] = cert
            return cert
        elif current_rejection_ratio > (1.0 - self.quorum_ratio):
            cert = {
                "proposal_id": proposal_id,
                "status": "REJECTED",
                "rejected_weight": rejected_weight,
                "total_weight": total_weight,
                "approval_ratio": current_approval_ratio
            }
            self.committed_proposals[proposal_id] = cert
            return cert
        else:
            return {
                "proposal_id": proposal_id,
                "status": "PENDING",
                "approved_weight": approved_weight,
                "total_weight": total_weight,
                "approval_ratio": current_approval_ratio
            }
