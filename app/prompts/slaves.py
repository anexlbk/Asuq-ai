"""Slave agent prompts (SHOWCASE).

Full prompt text is omitted from this public repo. The legal expert prompt
instructs the agent to answer based only on retrieved documents, never
fabricate citations, always cite specific article numbers with sources,
and include a mandatory disclaimer. Template placeholders ({query},
{rag_context}, {verified_citations}) are injected at runtime.
"""

LEGAL_EXPERT_SYSTEM = (
    "System prompt for the legal expert slave: answers Algerian law questions "
    "using retrieved context only. Never fabricates citations. Always includes "
    "a disclaimer. "
    "[Full prompt omitted — see internal docs.]"
)
