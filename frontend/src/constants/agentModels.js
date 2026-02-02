/**
 * Available LLM Agent Models
 * List of all available models that can be used across all agents
 */

export const AGENT_MODELS = [
  { id: "gpt-4", label: "GPT-4", provider: "openai" },
  { id: "gpt-4o", label: "GPT-4o", provider: "openai" },
  { id: "gpt-4o-mini-2024-07-18", label: "GPT-4o Mini", provider: "openai" },
  { id: "gpt-4.1-nano-2025-04-14", label: "GPT-4.1 Nano", provider: "openai" },
  { id: "gpt-4.1-mini-2025-04-14", label: "GPT-4.1 Mini", provider: "openai" },
  { id: "anthropic.claude-haiku-4-5-20251001-v1:0", label: "Claude Haiku 4.5", provider: "anthropic" },
  { id: "meta.llama4-scout-17b-instruct-v1:0", label: "Llama 4 Scout 17B", provider: "meta" },
  { id: "meta.llama4-maverick-17b-instruct-v1:0", label: "Llama 4 Maverick 17B", provider: "meta" },
  { id: "rlab-qwen3-32b", label: "Qwen3 32B", provider: "rlab" },
  { id: "gemini-2.0-flash-lite", label: "Gemini 2.0 Flash Lite", provider: "google" },
  { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash", provider: "google" },
  { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", provider: "google" },
  { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash", provider: "google" },
  { id: "gemini-3-flash-preview", label: "Gemini 3 Flash Preview", provider: "google" },
  { id: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash Lite", provider: "google" },
  { id: "claude-3-5-haiku@20241022", label: "Claude 3.5 Haiku", provider: "anthropic" },
  { id: "claude-sonnet-4@20250514", label: "Claude Sonnet 4", provider: "anthropic" },
  { id: "claude-haiku-4-5@20251001", label: "Claude Haiku 4.5", provider: "anthropic" },
  { id: "claude-sonnet-4-5@20250929", label: "Claude Sonnet 4.5", provider: "anthropic" },
  { id: "deepseek-r1", label: "DeepSeek R1", provider: "deepseek" },
  { id: "gpt-oss-120b", label: "GPT OSS 120B", provider: "openai" },
];

// Default model
export const DEFAULT_MODEL_ID = "gpt-4";

// Get model by ID
export const getModelById = (id) => AGENT_MODELS.find(model => model.id === id);

// Get model label by ID
export const getModelLabel = (id) => {
  const model = getModelById(id);
  return model ? model.label : id;
};

// Get provider color for styling
export const getProviderColor = (provider) => {
  const colors = {
    openai: '#10a37f',
    anthropic: '#d97706',
    meta: '#0668E1',
    google: '#4285F4',
    rlab: '#8b5cf6',
    deepseek: '#1e40af',
  };
  return colors[provider] || '#6b7280';
};

export default AGENT_MODELS;
