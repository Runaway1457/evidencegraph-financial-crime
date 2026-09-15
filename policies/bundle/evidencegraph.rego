package evidencegraph

import rego.v1

default authorize := {
    "allow": false,
    "reason": "policy denied action",
    "obligations": [],
}

allowed_actions := {
    "investigator": {"investigation.run": true},
    "reviewer": {"finding.review": true},
    "administrator": {
        "investigation.run": true,
        "finding.review": true,
    },
}

authorize := {
    "allow": true,
    "reason": "role and case assignment verified",
    "obligations": ["append_audit_event", "mask_pii"],
} if {
    input.actor_id != ""
    input.case_id != ""
    assignment := data.identity.assignments[input.actor_id]
    assignment.cases[_] == input.case_id
    allowed_actions[assignment.role][input.action]
}
