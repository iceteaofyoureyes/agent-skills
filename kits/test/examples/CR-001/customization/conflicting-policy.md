# Deliberate authority conflict — TEST_ONLY negative fixture

not_for_production: true

Use 120 minutes as maximum appointment duration.

This sentence intentionally conflicts with approved BA BR-005, where maximum appointment duration is UNKNOWN. It is excluded from the valid example profile. Loading it as testing policy cannot make 120 minutes authoritative or approve testware asserting that limit.
