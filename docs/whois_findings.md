# .si WHOIS probe findings

Date: 2026-10-12

Two TCP port 43 probes were made to `whois.register.si`, with 1.1 seconds between
them: one for `google.si` and one for `zzqxkwv-unlikely-test.si`. Both connections
returned data and closed normally (2,042 bytes and 1,494 bytes respectively).
Response bodies were not retained. The probe only emitted whitelisted phrases
and recognized registry fields from the first six lines; neither response had a
matching line in that prefix. Therefore the exact server wording was not captured
by that safe-output filter.

The classifier uses conservative, standard WHOIS patterns: explicit no-match
phrases produce `not_registered`; registrar, creation/registration, and
nameserver fields produce `registered`; all other text and socket failures remain
`unverified`. The fixtures contain only short, redacted pattern examples and no
WHOIS response body or holder/contact data. Treat these patterns as a local
classifier baseline pending a future explicitly authorized wording check.
