import os
from typing import Any, Dict
from langfuse import Langfuse
from langfuse.decorators import observe_llm

# Example: Azure OpenAI client (replace with your actual client)
from openai import AzureOpenAI

class LLMFormatter:
    """
    Formats agent findings, synthesis, and reflection using LLM.
    All LLM calls are traced via Langfuse for observability.
    """

    def __init__(self):
        # Langfuse setup
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY")
        )
        # Azure OpenAI setup (replace with your actual client/config)
        self.llm = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_base=os.getenv("AZURE_ENDPOINT"),
            api_version=os.getenv("API_VERSION", "2024-02-15-preview")
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4")

    @observe_llm(name="format_finding")
    def format_finding(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format a single agent's finding.
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(context)}
        ]
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=512
        )
        return response.choices[0].message.content

    @observe_llm(name="format_synthesis")
    def format_synthesis(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format synthesis (root cause) output.
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(context)}
        ]
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=512
        )
        return response.choices[0].message.content

    @observe_llm(name="format_reflection")
    def format_reflection(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format reflection (reasoning audit) output.
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(context)}
        ]
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=512
        )
        return response.choices[0].message.content

    # Optionally, add fallback logic if LLM fails
    def fallback_template(self, context: Dict[str, Any]) -> str:
        return f"Could not format output. Context: {context}"