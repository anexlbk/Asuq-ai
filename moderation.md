# Moderation

Four independent layers, each cheaper and coarser than the one after it, so most requests never
reach the expensive checks:

| Layer | Mechanism | Speed |
|---|---|---|
| 1 - Blocklist | Regex against a configurable term list | Microseconds |
| 2 - Toxicity classifier | `unitary/toxic-bert`, threshold-gated | Fast, local inference |
| 3 - LLM judge | Fast model checks hate speech, misinformation, spam, PII - approve / reject / queue | One LLM call |
| 4 - AI gate | Injection detection (input) + credential-leak detection (output), regex fast-path with an LLM deep check | Regex first, LLM only if ambiguous |

Layer 3 is deliberately conservative: uncertain cases route to a manual review queue rather than
auto-approving or auto-rejecting. A wrong auto-reject blocks a legitimate user; a wrong
auto-approve lets something bad through. Queuing trades latency (for the uncertain minority) for
correctness on both failure directions.

## Fail-closed (current behavior)

Security nodes are **fail-closed**: every internal error (timeout, model unavailable, unexpected
exception) results in `safe: False`, blocking the request. The error is always logged.

This was changed from fail-open to fail-closed to ensure that a transient dependency failure never
lets harmful content through. The tradeoff is that legitimate users may occasionally be blocked
during infrastructure blips, but this is preferable to the alternative for a production security
boundary.
