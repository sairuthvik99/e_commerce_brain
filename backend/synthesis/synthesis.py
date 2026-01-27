import json
from typing import Dict, Any, List
from backend.utils.llm_formatter import LLMFormatter
from backend.schemas.agent_output import AgentOutput
from backend.schemas.root_cause import RootCause

class SynthesisAgent:
    """
    Aggregates agent outputs into root cause analysis.
    """

    def __init__(self):
        self.formatter = LLMFormatter()
        # Load synthesis prompt from file
        with open("backend/synthesis/prompts/synthesis.md", "r") as f:
            self.synthesis_prompt = f.read()

    def synthesize(self, agent_outputs: Dict[str, AgentOutput]) -> RootCause:
        """
        Combine agent findings.
        Steps:
        1. Weight findings by confidence
        2. Identify causal relationships
        3. Build dependency graph
        4. Generate root cause narrative
        """
        # Prepare context for LLM
        findings = [
            {
                "agent": k,
                "finding": v.finding,
                "confidence": v.confidence,
                "evidence": v.evidence
            }
            for k, v in agent_outputs.items()
        ]
        context = {
            "findings": findings
        }
        # Call LLMFormatter (Langfuse-traced)
        synthesis_result = self.formatter.format_synthesis(
            prompt=self.synthesis_prompt,
            context=context
        )
        # Parse LLM output (assume JSON)
        try:
            result = json.loads(synthesis_result)
        except Exception:
            # Fallback: wrap as root cause
            result = {
                "root_cause": synthesis_result,
                "primary_cause": findings[0]["agent"] if findings else "",
                "contributing_causes": [f["agent"] for f in findings[1:]],
                "confidence": max([f["confidence"] for f in findings], default=0.8),
                "causal_chain": [f["agent"] for f in findings],
                "evidence_summary": {f["agent"]: f["evidence"] for f in findings}
            }
        return RootCause(**result)

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent_outputs = state.get("agent_outputs", {})
        root_cause = self.synthesize(agent_outputs)
        state["root_cause"] = root_cause.dict()
        state["causal_chain"] = root_cause.causal_chain
        return state