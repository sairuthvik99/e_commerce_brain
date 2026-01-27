"""
Prompt Loader Utility

Loads prompts from markdown files with YAML frontmatter.
Supports template variable substitution.
"""

import os
import re
from typing import Dict, Optional
from pathlib import Path
import yaml


class PromptLoader:
    """
    Centralized prompt loader that reads .md files with YAML frontmatter.
    
    Usage:
        loader = PromptLoader()
        prompt = loader.load("supervisor", "intent_classification", "system")
        prompt_with_vars = loader.load("supervisor", "intent_classification", "user", 
                                       variables={"question": "Why did sales drop?"})
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            base_path: Base directory for prompts. Defaults to backend/
        """
        if base_path is None:
            # Auto-detect base path (backend/)
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent  # backend/
        else:
            self.base_path = Path(base_path)
        
        self._cache: Dict[str, Dict] = {}
    
    def load(
        self, 
        agent: str, 
        task: str, 
        prompt_type: str, 
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Load a prompt from a markdown file.
        
        Args:
            agent: Agent name (e.g., "supervisor", "sales")
            task: Task name (e.g., "intent_classification")
            prompt_type: "system" or "user"
            variables: Optional dict for template variable substitution
        
        Returns:
            The loaded prompt string with variables substituted
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            ValueError: If prompt type not found in file
        """
        cache_key = f"{agent}:{task}"
        
        # Load from cache or file
        if cache_key not in self._cache:
            self._load_prompt_file(agent, task)
        
        # Get the specific prompt type
        prompts = self._cache.get(cache_key, {})
        if prompt_type not in prompts:
            raise ValueError(
                f"Prompt type '{prompt_type}' not found in {agent}/{task}. "
                f"Available types: {list(prompts.keys())}"
            )
        
        prompt = prompts[prompt_type]
        
        # Substitute variables if provided
        if variables:
            prompt = self._substitute_variables(prompt, variables)
        
        return prompt
    
    def _load_prompt_file(self, agent: str, task: str) -> None:
        """
        Load and parse a prompt markdown file with YAML frontmatter.
        
        Args:
            agent: Agent name
            task: Task name
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Construct file path: backend/agents/{agent}/prompts/{task}.md
        file_path = self.base_path / "agents" / agent / "prompts" / f"{task}.md"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {file_path}\n"
                f"Expected location: backend/agents/{agent}/prompts/{task}.md"
            )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by YAML frontmatter blocks (---)
        sections = self._parse_sections(content)
        
        cache_key = f"{agent}:{task}"
        self._cache[cache_key] = sections
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse markdown file with multiple YAML frontmatter sections.
        
        Returns:
            Dict mapping prompt_type to prompt content
        """
        # Split by --- delimiters
        parts = re.split(r'^---\s*$', content, flags=re.MULTILINE)
        
        sections = {}
        i = 1  # Skip first empty part
        
        while i < len(parts):
            # Parse YAML frontmatter
            if i >= len(parts):
                break
            
            frontmatter_text = parts[i].strip()
            if not frontmatter_text:
                i += 1
                continue
            
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse YAML frontmatter: {e}")
                i += 1
                continue
            
            # Get prompt content (next section)
            i += 1
            if i >= len(parts):
                break
            
            prompt_content = parts[i].strip()
            prompt_type = frontmatter.get('prompt_type', 'unknown')
            sections[prompt_type] = prompt_content
            
            i += 1
        
        return sections
    
    def _substitute_variables(self, prompt: str, variables: Dict[str, str]) -> str:
        """
        Substitute template variables in prompt.
        
        Supports {variable_name} syntax.
        
        Args:
            prompt: Prompt template string
            variables: Dict of variable names to values
        
        Returns:
            Prompt with variables substituted
        """
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def clear_cache(self) -> None:
        """Clear the prompt cache. Useful for testing or hot-reloading."""
        self._cache.clear()


# Singleton instance for easy import
_loader = PromptLoader()

def load_prompt(
    agent: str, 
    task: str, 
    prompt_type: str, 
    variables: Optional[Dict[str, str]] = None
) -> str:
    """
    Convenience function to load a prompt.
    
    Usage:
        from backend.utils.prompt_loader import load_prompt
        
        system_prompt = load_prompt("supervisor", "intent_classification", "system")
        user_prompt = load_prompt("supervisor", "intent_classification", "user", 
                                  variables={"question": "Why did sales drop?"})
    """
    return _loader.load(agent, task, prompt_type, variables)