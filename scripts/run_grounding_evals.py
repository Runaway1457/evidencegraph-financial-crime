#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any

from evidencegraph.application.grounding import validate_proposal
from evidencegraph.application.ports import AgentFindingProposal
from evidencegraph.domain.errors import DomainError


def evaluate(path: Path) -> dict[str, Any]:
    total = passed = false_accepts = false_rejects = 0
    cases: list[dict[str, object]] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        proposal = AgentFindingProposal(
            title=record["title"],
            rationale=record["rationale"],
            evidence_ids=tuple(record["evidence_ids"]),
            confidence=float(record["confidence"]),
        )
        try:
            validate_proposal(proposal, known_evidence=set(record["known_evidence"]))
            accepted = True
            reason = "accepted"
        except DomainError as exc:
            accepted = False
            reason = str(exc)

        expected = bool(record["expected_accept"])
        matched = accepted == expected
        total += 1
        passed += int(matched)
        false_accepts += int(accepted and not expected)
        false_rejects += int(not accepted and expected)
        cases.append(
            {
                "id": record["id"],
                "expected_accept": expected,
                "accepted": accepted,
                "matched": matched,
                "reason": reason,
            }
        )

    return {
        "suite": "grounding-gate-v1",
        "total": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "false_accepts": false_accepts,
        "false_rejects": false_rejects,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    result = evaluate(args.dataset)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"grounding-gate: {result['passed']}/{result['total']} passed; "
        f"false_accepts={result['false_accepts']}; "
        f"false_rejects={result['false_rejects']}"
    )
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
