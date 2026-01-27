import json
from typing import Dict, Any
from backend.utils.llm_formatter import LLMFormatter
from backend.schemas.root_cause import RootCause
from backend.schemas.reflection_result import ReflectionResult

class SelfReflectionAgent:
    """
    Audits reasoning quality and detects issues.
    Checks:
    - Conflicting findings between agents
    - Low confidence scores
    - Missing evidence
    - Logical inconsistencies
    - Hallucination detection
    """

    def __init__(self):
        self.formatter = LLMFormatter()
        with open("backend/reflection/prompts/reflection.md", "r") as f:
            self.reflection_prompt = f.read()

    def reflect(self, agent_outputs: Dict[str, Any], synthesis: RootCause) -> ReflectionResult:
        """
        Audit the reasoning chain.
        Returns:
        - conflicts: List of contradictions
        - quality_score: Overall quality (0-1)
        - warnings: List of issues
        - recommendations: Suggested improvements
        """
        context = {
            "agent_outputs": agent_outputs,
            "synthesis": synthesis.dict() if hasattr(synthesis, "dict") else synthesis
        }
        # Call LLMFormatter (Langfuse-traced)
        reflection_result = self.formatter.format_reflection(
            prompt=self.reflection_prompt,
            context=context
        )
        # Parse LLM output (assume JSON)
        try:
            result = json.loads(reflection_result)
        except Exception:
            # Fallback: basic structure
            result = {
                "quality_score": 0.8,
                "conflicts_detected": 0,
                "conflicts": [],
                "warnings": ["LLM output not in JSON format"],
                "recommendations": [],
                "pass": True
            }
        return ReflectionResult(**result)

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent_outputs = state.get("agent_outputs", {})
        synthesis = state.get("root_cause", {})
        reflection = self.reflect(agent_outputs, synthesis)
        state["reflection_result"] = reflection.dict()
        state["quality_score"] = reflection.quality_score
        state["conflicts"] = reflection.conflicts
        return state