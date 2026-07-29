"""Principal prompts (SHOWCASE).

Full prompt text is omitted from this public repo. In production the planner
prompt instructs the model to decompose user requests into a sequence of
subtasks for registered slave agents and return a JSON plan. The synthesizer
prompt instructs the model to combine slave outputs into a coherent response,
preserving legal disclaimers and citations when the legal_expert slave was used.
"""

PRINCIPAL_PLANNER_SYSTEM = (
    "System prompt for the planner agent: decomposes user requests into "
    "a JSON task plan using registered slave agents. "
    "[Full prompt omitted — see internal docs.]"
)

PRINCIPAL_SYNTHESIZER_SYSTEM = (
    "System prompt for the synthesizer agent: combines outputs from multiple "
    "slave agents into a coherent final response. Preserves legal disclaimers "
    "and citations when legal_expert is among the slaves. "
    "[Full prompt omitted — see internal docs.]"
)
