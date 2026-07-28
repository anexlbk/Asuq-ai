"""Shared state definition for the LangGraph state machine."""
from typing import TypedDict, List, Dict, Any, Optional


class AsuqState(TypedDict):
    user_id: str
    session_id: str
    raw_input: str
    script_type: str
    current_normalized_input: str
    normalized_input: str
    language_override: Optional[str]
    chat_history: List[str]
    intent: str
    selected_skill: str
    routing_confidence: float
    skill_output: Dict[str, Any]
    product_image_url: Optional[str]
    landing_page_preferences: dict
    landing_page_output: dict
    rag_context: List[str]
    memory_context: List[str]
    llm_response: str
    proposed_response: str
    response_type: str
    final_output: Dict[str, Any]
    plan: List[Dict[str, Any]]
    slave_results: Dict[str, Any]
    requirements_result: Dict[str, Any]
    security_input_result: Dict[str, Any]
    security_output_result: Dict[str, Any]
    reflection_result: Dict[str, Any]
    reviewer_score: float
    needs_retry: bool
    clarification_questions: List[str]
    error: Optional[str]
    retry_count: int
    low_confidence_flag: bool
    quality_exhausted: bool
    leaned_from_mistake: Optional[str]
    has_prompt_intent: bool
    document_id: Optional[str]
    is_simple: bool
    is_simple_content: bool
    weakest_dimension: Optional[str]
    improvement_instructions: Optional[str]
    prompt_rating: Optional[float]
    is_world_query: bool
    status_message: str
    deprioritized: List[Dict[str, str]]
