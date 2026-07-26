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

## Fail-open, on purpose

Every security node defaults to **allow-through** if it hits an internal error - timeout, model
unavailable, unexpected exception - rather than blocking the user. The error is always logged.

This is a real product tradeoff, not an oversight: a marketing assistant that goes down whenever
a moderation dependency has a bad moment is worse for most users than one that occasionally lets
a borderline message through during a transient failure. The fail-open behavior is scoped
tightly - it only triggers on infrastructure/internal errors, never on a positive detection.
A message that layer 2 or 3 actually flags is blocked; a message that layer 2 or 3 *couldn't
evaluate* is allowed and logged for review.

Changing this default from fail-open to fail-closed is a one-line change in each node, but it's a
product decision with real availability consequences, made deliberately and revisited only
explicitly.
