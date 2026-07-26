"""Shared state definition for the LangGraph state machine."""
from typing import TypedDict, List, Dict, Any, Optional


class AsuqState(TypedDict):
    """Shared state across all nodes in the LangGraph.

    This state is checkpointed to Postgres after each node execution,
    allowing conversation recovery and time-travel debugging.
    """
    # User & Session
    user_id: str
    session_id: str

    # Input
    raw_input: str
    script_type: str  # 'arabic' | 'franco' | 'mixed' | 'french' | 'english'
    current_normalized_input: str  # current-turn normalized text only (no chat_history prefix)
    normalized_input: str
    language_override: Optional[str]  # 'en' | 'fr' | 'ar' from sticky facts
    chat_history: List[str]  # last N messages from current session

    # Routing
    intent: str
    selected_skill: str
    routing_confidence: float

    # Skill Execution
    skill_output: Dict[str, Any]

    # Landing Page
    product_image_url: Optional[str]
    landing_page_preferences: dict
    landing_page_output: dict

    # Context
    rag_context: List[str]
    memory_context: List[str]

    # LLM
    llm_response: str
    proposed_response: str  # response before output security check

    # Output
    response_type: str  # 'text' | 'image' | 'structured_plan' | 'error'
    final_output: Dict[str, Any]

    # Multi-agent (Principal + Slaves)
    plan: List[Dict[str, Any]]  # task plan: [{slave_name, instructions, ...}]
    slave_results: Dict[str, Any]  # {slave_name: {result, metadata, error}}

    # Requirements Analysis (prompt quality gate)
    requirements_result: Dict[str, Any]  # {intent_understood, information_complete, ...}

    # Security Analysis (input + output)
    security_input_result: Dict[str, Any]  # {safe, reason, block_category}
    security_output_result: Dict[str, Any]  # {safe, reason, leak_category}

    # Reflection Analysis (post-response quality & correction learning)
    reflection_result: Dict[str, Any]  # {quality_score, lessons, corrections, ...}

    # Self-correction loop
    reviewer_score: float  # 0-10 score from latest reviewer pass
    needs_retry: bool  # quality_gate sets True when reviewer score < threshold

    # Clarification (multi-turn detail gathering)
    clarification_questions: List[str]  # Generated clarifying questions; empty = proceed

    # Error handling
    error: Optional[str]
    retry_count: int

    # Routing flags
    low_confidence_flag: bool  # set when routing confidence is in mid-range
    quality_exhausted: bool  # set when max self-correction passes used

    # Query classification
    leaned_from_mistake: Optional[str]  # correction fact from reflection agent
    has_prompt_intent: bool  # whether the query has a clear task intent
    document_id: Optional[str]  # active uploaded document reference
    is_simple: bool  # greeting / thanks that bypasses full pipeline
    is_simple_content: bool  # short content request using fast lane

    # Quality gate fields (returned by quality_gate_node)
    weakest_dimension: Optional[str]
    improvement_instructions: Optional[str]

    # Prompt rating (returned by prompt_rating_node)
    prompt_rating: Optional[float]  # 1-5 rating of user query quality

    # World / general knowledge query (not about the core domain)
    is_world_query: bool

    # Real-time status message shown to user during processing
    status_message: str

    # Planner disclosure - tasks the planner considered but cut (max 5 hard limit)
    deprioritized: List[Dict[str, str]]
