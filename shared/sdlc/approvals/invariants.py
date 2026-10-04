"""Approved invariants. Hashes bind integrity/provenance, not Human identity."""
AUTHORITY_PRECEDENCE = (
    "Human-approved decisions", "Shared SDLC invariants", "Project Policy",
    "Kit / skill instructions", "Runtime defaults",
)
APPROVAL_INVARIANTS = (
    "CONTINUE != APPROVE", "ANSWER != APPROVE", "validator PASS != APPROVE",
    "artifact generated != APPROVED", "derived artifact != authority",
    "CURRENT_SYSTEM != approved target business rule", "Dev fix PASS != Tester VERIFIED",
)
