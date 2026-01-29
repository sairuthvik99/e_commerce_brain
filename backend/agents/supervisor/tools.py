"""
Supervisor Agent LangChain Tools

NOTE: This file is deprecated and not in use.
The supervisor agent now uses a simpler LLM-based approach without tools.
These tools are kept for reference and potential future use.

To delete this file, remove it manually after confirming the supervisor
agent works correctly without it.
"""

# =============================================================================
# DEPRECATED - ALL CODE BELOW IS COMMENTED OUT
# =============================================================================

# from langchain_core.tools import tool
# from langchain_openai import AzureChatOpenAI
# from pydantic import BaseModel, Field
# from typing import Dict, Any, Optional, List
# from backend.settings import Settings
# from backend.utils.prompt_loader import load_prompt
# from langfuse import observe
# import json
# import logging

# logger = logging.getLogger(__name__)


# # ==================== Pydantic Input Schemas ====================

# class IntentClassificationInput(BaseModel):
#     """Input schema for intent classification."""
#     question: str = Field(description="The user's question to classify")


# class AgentRoutingInput(BaseModel):
#     """Input schema for agent routing decisions."""
#     question: str = Field(description="The user's question")
#     intent: str = Field(description="Classified intent from intent detection")


# class CrossDomainAnalysisInput(BaseModel):
#     """Input schema for cross-domain analysis."""
#     question: str = Field(description="The user's question requiring multi-domain analysis")
#     domains: List[str] = Field(
#         default=["sales", "inventory", "marketing", "support"],
#         description="Domains to analyze"
#     )


# class MemoryQueryInput(BaseModel):
#     """Input schema for memory/history queries."""
#     question: str = Field(description="Question about past incidents or actions")
#     query_type: str = Field(
#         default="similar_incidents",
#         description="Type: similar_incidents, past_actions, effectiveness"
#     )


# class ActionRecommendationInput(BaseModel):
#     """Input schema for action recommendations."""
#     question: str = Field(description="The action-oriented question/command")
#     findings: Dict[str, Any] = Field(
#         default_factory=dict,
#         description="Findings from domain agents"
#     )


# class SummaryReportInput(BaseModel):
#     """Input schema for summary/report generation."""
#     question: str = Field(description="The reporting question")
#     report_type: str = Field(
#         default="executive_summary",
#         description="Type: executive_summary, detailed, recommendations"
#     )
#     findings: Dict[str, Any] = Field(
#         default_factory=dict,
#         description="Findings from all agents"
#     )


# # ==================== LLM Helper ====================

# class SupervisorLLMHelper:
#     """Helper class for supervisor LLM operations."""
    
#     def __init__(self):
#         self.llm = AzureChatOpenAI(
#             api_key=Settings.DIAL_API_KEY,
#             azure_endpoint=Settings.AZURE_ENDPOINT,
#             api_version=Settings.API_VERSION,
#             model=Settings.AGENT_MODELS.get("supervisor", "gpt-4"),
#             temperature=0.1,
#         )
#         logger.info("[SupervisorLLMHelper] Initialized")
    
#     @observe(name="supervisor_llm_analyze")
#     def analyze(
#         self,
#         question: str,
#         context: Dict[str, Any],
#         analysis_type: str
#     ) -> Dict[str, Any]:
#         """General LLM analysis for supervisor tasks."""
#         try:
#             system_prompt = f"""You are an E-commerce Operations Supervisor AI.
# You help route questions to appropriate domain agents and synthesize multi-domain insights.

# Analysis type: {analysis_type}

# Respond with a valid JSON object."""

#             user_prompt = f"""Question: {question}

# Context:
# {json.dumps(context, indent=2, default=str)}

# Provide your analysis as JSON."""

#             messages = [
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ]
            
#             response = self.llm.invoke(messages)
#             content = response.content.strip()
            
#             try:
#                 if content.startswith("```"):
#                     content = content.split("```")[1]
#                     if content.startswith("json"):
#                         content = content[4:]
#                     content = content.strip()
#                 return json.loads(content)
#             except json.JSONDecodeError:
#                 return {"result": content}
                
#         except Exception as e:
#             logger.error(f"[SupervisorLLMHelper] Analysis failed: {e}")
#             return {"error": str(e)}


# # Global helper instance
# _helper: Optional[SupervisorLLMHelper] = None

# def get_helper() -> SupervisorLLMHelper:
#     """Get or create the global helper instance."""
#     global _helper
#     if _helper is None:
#         _helper = SupervisorLLMHelper()
#     return _helper


# # ==================== Tools (All Commented Out) ====================
# # @tool("classify_user_intent", args_schema=IntentClassificationInput)
# # def classify_user_intent(question: str) -> Dict[str, Any]:
# #     ...

# # @tool("determine_agents_to_call", args_schema=AgentRoutingInput)
# # def determine_agents_to_call(question: str, intent: str) -> Dict[str, Any]:
# #     ...

# # ... (remaining tools commented out)


# def get_supervisor_tools() -> List:
#     """DEPRECATED: Returns empty list. Tools are no longer used."""
#     return []


# def get_tool_descriptions() -> Dict[str, str]:
#     """DEPRECATED: Returns empty dict. Tools are no longer used."""
#     return {}

# =============================================================================
# END OF DEPRECATED CODE
# =============================================================================
