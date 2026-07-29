"""
AsuqState - reference schema.

Public reference reflecting the shape of the production state object, not copy-pasted
production source. Field names and grouping are accurate; this file has no business logic.

Every node in the graph reads a subset of this state and writes a subset back. Adding a field
means updating this schema AND every node that should populate or consume it - the graph has no
implicit field discovery.
"""

from typing import TypedDict, Any, Optional


class AsuqState(TypedDict, total=False):
    # User & session
    user_id: str
    session_id: str

    # Input
    raw_input: str
    normalized_input: str
    script_type: str  # "arabic" | "french" | "english" | "franco" | "mixed"
    darija_confidence: float  # 0.0-1.0 confidence that input is Darija
    chat_history: list[dict[str, Any]]

    # Routing
    intent: str
    selected_skill: str
    routing_confidence: float

    # Context
    rag_context: list[str]
    memory_context: list[str]

    # Skill output
    skill_output: dict[str, Any]

    # Landing page
    product_image_url: Optional[str]
    landing_page_preferences: dict[str, Any]
    landing_page_output: dict[str, Any]

    # LLM
    llm_response: str
    proposed_response: str

    # Planning / execution
    plan: list[dict[str, Any]]
    slave_results: dict[str, Any]

    # Security
    security_input_result: dict[str, Any]
    security_output_result: dict[str, Any]

    # Quality
    reviewer_score: float
    quality_exhausted: bool
    weakest_dimension: Optional[str]

    # Clarification
    clarification_questions: list[str]

    # Reflection
    reflection_result: dict[str, Any]

    # Error handling
    error: Optional[str]
    retry_count: int

    # Flags
    is_simple: bool
    is_simple_content: bool
    is_world_query: bool
    low_confidence_flag: bool

    # Output
    response_type: str  # "text" | "image" | "structured_plan" | "error"
    final_output: dict[str, Any]
    status_message: Optional[str]
