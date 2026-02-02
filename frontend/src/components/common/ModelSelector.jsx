import { useState } from 'react';
import { useModel } from '../../context/ModelContext';
import { getModelById, getProviderColor } from '../../constants/agentModels';
import ConfirmModal from './ConfirmModal';
import './ModelSelector.css';

/**
 * Model Selector Component
 * Dropdown for selecting the LLM model with confirmation modal
 */
function ModelSelector() {
  const { currentModelId, currentModel, models, changeModel, isLoading } = useModel();
  const [pendingModelId, setPendingModelId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSelectChange = (e) => {
    const newModelId = e.target.value;
    if (newModelId !== currentModelId) {
      setPendingModelId(newModelId);
      setIsModalOpen(true);
    }
  };

  const handleConfirm = async () => {
    if (pendingModelId) {
      const success = await changeModel(pendingModelId);
      if (success) {
        setIsModalOpen(false);
        setPendingModelId(null);
      }
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setPendingModelId(null);
  };

  const pendingModel = pendingModelId ? getModelById(pendingModelId) : null;

  // Group models by provider for better organization
  const groupedModels = models.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = [];
    }
    acc[model.provider].push(model);
    return acc;
  }, {});

  const providerOrder = ['openai', 'anthropic', 'google', 'meta', 'deepseek', 'rlab'];
  const providerLabels = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    google: 'Google',
    meta: 'Meta',
    deepseek: 'DeepSeek',
    rlab: 'Research Lab',
  };

  return (
    <>
      <div className="model-selector">
        <label className="model-label" htmlFor="model-select">
          Model
        </label>
        <div className="model-select-wrapper">
          <span 
            className="provider-indicator"
            style={{ backgroundColor: getProviderColor(currentModel?.provider) }}
          />
          <select
            id="model-select"
            className="model-select"
            value={currentModelId}
            onChange={handleSelectChange}
            disabled={isLoading}
          >
            {providerOrder.map(provider => {
              const providerModels = groupedModels[provider];
              if (!providerModels || providerModels.length === 0) return null;
              
              return (
                <optgroup key={provider} label={providerLabels[provider]}>
                  {providerModels.map(model => (
                    <option key={model.id} value={model.id}>
                      {model.label}
                    </option>
                  ))}
                </optgroup>
              );
            })}
          </select>
        </div>
      </div>

      <ConfirmModal
        isOpen={isModalOpen}
        onClose={handleCancel}
        onConfirm={handleConfirm}
        currentModel={currentModel}
        newModel={pendingModel}
        isLoading={isLoading}
      />
    </>
  );
}

export default ModelSelector;
