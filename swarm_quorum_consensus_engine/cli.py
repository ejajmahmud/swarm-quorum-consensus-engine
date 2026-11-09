"""CLI for swarm-quorum-consensus-engine."""
import sys
import argparse
from .engine import SwarmQuorumEngine


def main():
    parser = argparse.ArgumentParser(description="Swarm Quorum Consensus Engine CLI")
    parser.add_argument("--demo", action="store_true", help="Run consensus demonstration with 3 agents")
    args = parser.parse_args()

    if args.demo:
        engine = SwarmQuorumEngine(quorum_ratio=0.66)
        engine.register_agent("agent_1", weight=1.0)
        engine.register_agent("agent_2", weight=1.0)
        engine.register_agent("agent_3", weight=1.5)

        prop = engine.submit_proposal("prop_001", "execute_sql_migration", {"table": "users"}, "agent_1")
        print(f"Submitted proposal: {prop.proposal_id} ({prop.action})")

        engine.cast_vote("agent_1", prop.proposal_id, approve=True)
        engine.cast_vote("agent_3", prop.proposal_id, approve=True)

        res = engine.evaluate_quorum(prop.proposal_id)
        print(f"Consensus Result: {res['status']} (Approval Ratio: {res['approval_ratio']:.1%})")
        if res['status'] == "COMMITTED":
            print(f"  Quorum Certificate Hash: {res['certificate_hash']}")
    else:
        parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
