package evidencegraph

import rego.v1

test_assigned_investigator_can_run if {
    result := authorize with input as {
        "actor_id": "analyst_1",
        "action": "investigation.run",
        "case_id": "case_1",
    }
    result.allow
    result.obligations == ["append_audit_event", "mask_pii"]
}

test_unassigned_case_is_denied if {
    result := authorize with input as {
        "actor_id": "analyst_1",
        "action": "investigation.run",
        "case_id": "case_2",
    }
    not result.allow
}

test_investigator_cannot_review if {
    result := authorize with input as {
        "actor_id": "analyst_1",
        "action": "finding.review",
        "case_id": "case_1",
    }
    not result.allow
}

test_independent_reviewer_can_review if {
    result := authorize with input as {
        "actor_id": "reviewer_2",
        "action": "finding.review",
        "case_id": "case_1",
    }
    result.allow
}
