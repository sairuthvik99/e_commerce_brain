import { useState, useEffect, useCallback } from 'react';
import apiService from '../../services/api';
import HistoryIcon from '@mui/icons-material/History';
import StorageIcon from '@mui/icons-material/Storage';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import SettingsIcon from '@mui/icons-material/Settings';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import SchoolIcon from '@mui/icons-material/School';
import './MemoryPage.css';

/**
 * Memory Page - View Short-Term and Long-Term Memory
 * Displays conversation history and stored preferences/facts/knowledge
 */
function MemoryPage() {
  const [activeTab, setActiveTab] = useState('short-term');
  const [shortTermData, setShortTermData] = useState(null);
  const [longTermData, setLongTermData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [clearing, setClearing] = useState(false);

  const fetchShortTermMemory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getShortTermMemory(10);
      setShortTermData(data);
    } catch (err) {
      setError(`Failed to load short-term memory: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLongTermMemory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getLongTermMemory();
      setLongTermData(data);
    } catch (err) {
      setError(`Failed to load long-term memory: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'short-term') {
      fetchShortTermMemory();
    } else {
      fetchLongTermMemory();
    }
  }, [activeTab, fetchShortTermMemory, fetchLongTermMemory]);

  const handleRefresh = () => {
    if (activeTab === 'short-term') {
      fetchShortTermMemory();
    } else {
      fetchLongTermMemory();
    }
  };

  const handleClear = async () => {
    const confirmMessage = activeTab === 'short-term'
      ? 'Are you sure you want to clear all conversation history?'
      : 'Are you sure you want to clear all long-term memory? This will delete preferences, facts, and knowledge.';
    
    if (!window.confirm(confirmMessage)) return;

    setClearing(true);
    try {
      if (activeTab === 'short-term') {
        await apiService.clearShortTermMemory();
        setShortTermData({ entries: [], total_count: 0, max_entries: 10, message: 'Memory cleared' });
      } else {
        await apiService.clearLongTermMemory();
        setLongTermData({ preferences: [], facts: [], knowledge: [], message: 'Memory cleared' });
      }
    } catch (err) {
      setError(`Failed to clear memory: ${err.message}`);
    } finally {
      setClearing(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const truncateText = (text, maxLength = 150) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="memory-page">
      <div className="memory-container">
        {/* Header */}
        <div className="memory-header">
          <div className="header-title">
            <StorageIcon className="header-icon" sx={{ fontSize: 28 }} />
            <h1>Memory Store</h1>
          </div>
          <div className="header-actions">
            <button 
              className="header-btn refresh-btn"
              onClick={handleRefresh}
              disabled={loading}
              title="Refresh"
            >
              <RefreshIcon sx={{ fontSize: 20 }} />
              <span>Refresh</span>
            </button>
            <button 
              className="header-btn clear-btn"
              onClick={handleClear}
              disabled={loading || clearing}
              title="Clear Memory"
            >
              <DeleteIcon sx={{ fontSize: 20 }} />
              <span>{clearing ? 'Clearing...' : 'Clear'}</span>
            </button>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="memory-tabs">
          <button
            className={`memory-tab ${activeTab === 'short-term' ? 'active' : ''}`}
            onClick={() => setActiveTab('short-term')}
          >
            <HistoryIcon sx={{ fontSize: 20 }} />
            <span>Short-Term Memory</span>
            {shortTermData && (
              <span className="tab-badge">{shortTermData.total_count}</span>
            )}
          </button>
          <button
            className={`memory-tab ${activeTab === 'long-term' ? 'active' : ''}`}
            onClick={() => setActiveTab('long-term')}
          >
            <StorageIcon sx={{ fontSize: 20 }} />
            <span>Long-Term Memory</span>
            {longTermData && (
              <span className="tab-badge">
                {(longTermData.preferences?.length || 0) + 
                 (longTermData.facts?.length || 0) + 
                 (longTermData.knowledge?.length || 0)}
              </span>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="memory-error">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="memory-loading">
            <div className="loading-spinner"></div>
            <span>Loading memory...</span>
          </div>
        )}

        {/* Content */}
        {!loading && (
          <div className="memory-content">
            {activeTab === 'short-term' ? (
              <ShortTermMemoryView data={shortTermData} formatTimestamp={formatTimestamp} truncateText={truncateText} />
            ) : (
              <LongTermMemoryView data={longTermData} formatTimestamp={formatTimestamp} truncateText={truncateText} onRefresh={fetchLongTermMemory} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Short-Term Memory View Component
 */
function ShortTermMemoryView({ data, formatTimestamp, truncateText }) {
  if (!data || !data.entries || data.entries.length === 0) {
    return (
      <div className="memory-empty">
        <HistoryIcon sx={{ fontSize: 48 }} />
        <h3>No Conversation History</h3>
        <p>Start a conversation with the agent to build memory</p>
      </div>
    );
  }

  return (
    <div className="short-term-view">
      <div className="section-header">
        <QuestionAnswerIcon sx={{ fontSize: 20 }} />
        <h2>Conversation History</h2>
        <span className="section-count">{data.entries.length} / {data.max_entries} entries</span>
      </div>
      
      <div className="conversation-list">
        {data.entries.map((entry, index) => (
          <div key={entry.id || index} className="conversation-entry">
            <div className="entry-header">
              <span className="entry-number">#{index + 1}</span>
              <span className="entry-timestamp">{formatTimestamp(entry.timestamp)}</span>
              {entry.intent && <span className="entry-intent">{entry.intent}</span>}
            </div>
            <div className="entry-content">
              <div className="entry-question">
                <strong>Q:</strong> {entry.question}
              </div>
              <div className="entry-response">
                <strong>A:</strong> {truncateText(entry.response, 300)}
              </div>
            </div>
            {entry.agent_outputs && (
              <div className="entry-agents">
                <span className="agents-label">Agents involved:</span>
                {Object.keys(entry.agent_outputs).map(agent => (
                  <span key={agent} className="agent-tag">{agent}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Long-Term Memory View Component
 */
function LongTermMemoryView({ data, formatTimestamp, truncateText, onRefresh }) {
  const [expandedSection, setExpandedSection] = useState('preferences');
  const [showAddForm, setShowAddForm] = useState(null); // 'preference', 'fact', 'knowledge'
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  
  // Form states
  const [prefKey, setPrefKey] = useState('');
  const [prefValue, setPrefValue] = useState('');
  const [factText, setFactText] = useState('');
  const [factCategory, setFactCategory] = useState('general');
  const [knowledgeTopic, setKnowledgeTopic] = useState('');
  const [knowledgeContent, setKnowledgeContent] = useState('');

  const resetForms = () => {
    setPrefKey('');
    setPrefValue('');
    setFactText('');
    setFactCategory('general');
    setKnowledgeTopic('');
    setKnowledgeContent('');
    setFormError(null);
  };

  const handleSavePreference = async (e) => {
    e.preventDefault();
    if (!prefKey.trim() || !prefValue.trim()) {
      setFormError('Both key and value are required');
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await apiService.savePreference(prefKey.trim(), prefValue.trim());
      resetForms();
      setShowAddForm(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      setFormError(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveFact = async (e) => {
    e.preventDefault();
    if (!factText.trim() || factText.trim().length < 5) {
      setFormError('Fact must be at least 5 characters');
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await apiService.saveFact(factText.trim(), factCategory);
      resetForms();
      setShowAddForm(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      setFormError(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveKnowledge = async (e) => {
    e.preventDefault();
    if (!knowledgeTopic.trim() || knowledgeTopic.trim().length < 3) {
      setFormError('Topic must be at least 3 characters');
      return;
    }
    if (!knowledgeContent.trim() || knowledgeContent.trim().length < 10) {
      setFormError('Content must be at least 10 characters');
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await apiService.saveKnowledge(knowledgeTopic.trim(), knowledgeContent.trim(), 'user');
      resetForms();
      setShowAddForm(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      setFormError(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const hasPreferences = data?.preferences && data.preferences.length > 0;
  const hasFacts = data?.facts && data.facts.length > 0;
  const hasKnowledge = data?.knowledge && data.knowledge.length > 0;

  return (
    <div className="long-term-view">
      {/* Add Form Modal */}
      {showAddForm && (
        <div className="add-form-overlay" onClick={() => { setShowAddForm(null); resetForms(); }}>
          <div className="add-form-modal" onClick={(e) => e.stopPropagation()}>
            {showAddForm === 'preference' && (
              <>
                <h3>Add Preference</h3>
                <form onSubmit={handleSavePreference}>
                  <div className="form-group">
                    <label>Key</label>
                    <input 
                      type="text" 
                      value={prefKey} 
                      onChange={(e) => setPrefKey(e.target.value)}
                      placeholder="e.g., theme, language, default_model"
                    />
                  </div>
                  <div className="form-group">
                    <label>Value</label>
                    <input 
                      type="text" 
                      value={prefValue} 
                      onChange={(e) => setPrefValue(e.target.value)}
                      placeholder="e.g., dark, english, gpt-4"
                    />
                  </div>
                  {formError && <div className="form-error">{formError}</div>}
                  <div className="form-actions">
                    <button type="button" className="cancel-btn" onClick={() => { setShowAddForm(null); resetForms(); }}>Cancel</button>
                    <button type="submit" className="save-btn" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                  </div>
                </form>
              </>
            )}
            {showAddForm === 'fact' && (
              <>
                <h3>Add Fact</h3>
                <form onSubmit={handleSaveFact}>
                  <div className="form-group">
                    <label>Fact</label>
                    <textarea 
                      value={factText} 
                      onChange={(e) => setFactText(e.target.value)}
                      placeholder="e.g., The company holiday is on December 25th"
                      rows={3}
                    />
                  </div>
                  <div className="form-group">
                    <label>Category</label>
                    <select value={factCategory} onChange={(e) => setFactCategory(e.target.value)}>
                      <option value="general">General</option>
                      <option value="user_info">User Info</option>
                      <option value="business_rule">Business Rule</option>
                      <option value="product">Product</option>
                      <option value="customer">Customer</option>
                    </select>
                  </div>
                  {formError && <div className="form-error">{formError}</div>}
                  <div className="form-actions">
                    <button type="button" className="cancel-btn" onClick={() => { setShowAddForm(null); resetForms(); }}>Cancel</button>
                    <button type="submit" className="save-btn" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                  </div>
                </form>
              </>
            )}
            {showAddForm === 'knowledge' && (
              <>
                <h3>Add Knowledge</h3>
                <form onSubmit={handleSaveKnowledge}>
                  <div className="form-group">
                    <label>Topic</label>
                    <input 
                      type="text" 
                      value={knowledgeTopic} 
                      onChange={(e) => setKnowledgeTopic(e.target.value)}
                      placeholder="e.g., Sales Best Practices"
                    />
                  </div>
                  <div className="form-group">
                    <label>Content</label>
                    <textarea 
                      value={knowledgeContent} 
                      onChange={(e) => setKnowledgeContent(e.target.value)}
                      placeholder="Detailed knowledge or insight..."
                      rows={4}
                    />
                  </div>
                  {formError && <div className="form-error">{formError}</div>}
                  <div className="form-actions">
                    <button type="button" className="cancel-btn" onClick={() => { setShowAddForm(null); resetForms(); }}>Cancel</button>
                    <button type="submit" className="save-btn" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* Preferences Section */}
      <div className="ltm-section">
        <div 
          className={`section-header clickable ${expandedSection === 'preferences' ? 'expanded' : ''}`}
          onClick={() => setExpandedSection(expandedSection === 'preferences' ? '' : 'preferences')}
        >
          <SettingsIcon sx={{ fontSize: 20 }} />
          <h2>Preferences</h2>
          <span className="section-count">{data?.preferences?.length || 0} items</span>
          <button 
            className="add-btn"
            onClick={(e) => { e.stopPropagation(); setShowAddForm('preference'); }}
            title="Add Preference"
          >
            <AddIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        {expandedSection === 'preferences' && (
          <div className="section-content">
            {!hasPreferences ? (
              <div className="section-empty">No preferences stored. Click + to add one.</div>
            ) : (
              <div className="preference-list">
                {data.preferences.map((pref, index) => (
                  <div key={index} className="preference-item">
                    <span className="pref-key">{pref.key}</span>
                    <span className="pref-value">{JSON.stringify(pref.value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Facts Section */}
      <div className="ltm-section">
        <div 
          className={`section-header clickable ${expandedSection === 'facts' ? 'expanded' : ''}`}
          onClick={() => setExpandedSection(expandedSection === 'facts' ? '' : 'facts')}
        >
          <LightbulbIcon sx={{ fontSize: 20 }} />
          <h2>Facts</h2>
          <span className="section-count">{data?.facts?.length || 0} items</span>
          <button 
            className="add-btn"
            onClick={(e) => { e.stopPropagation(); setShowAddForm('fact'); }}
            title="Add Fact"
          >
            <AddIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        {expandedSection === 'facts' && (
          <div className="section-content">
            {!hasFacts ? (
              <div className="section-empty">No facts stored. Click + to add one.</div>
            ) : (
              <div className="facts-list">
                {data.facts.map((fact, index) => (
                  <div key={index} className="fact-item">
                    <div className="fact-header">
                      <span className="fact-category">{fact.category}</span>
                      <span className="fact-time">{formatTimestamp(fact.created_at)}</span>
                    </div>
                    <div className="fact-content">{fact.fact}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Knowledge Section */}
      <div className="ltm-section">
        <div 
          className={`section-header clickable ${expandedSection === 'knowledge' ? 'expanded' : ''}`}
          onClick={() => setExpandedSection(expandedSection === 'knowledge' ? '' : 'knowledge')}
        >
          <SchoolIcon sx={{ fontSize: 20 }} />
          <h2>Knowledge</h2>
          <span className="section-count">{data?.knowledge?.length || 0} items</span>
          <button 
            className="add-btn"
            onClick={(e) => { e.stopPropagation(); setShowAddForm('knowledge'); }}
            title="Add Knowledge"
          >
            <AddIcon sx={{ fontSize: 18 }} />
          </button>
        </div>
        {expandedSection === 'knowledge' && (
          <div className="section-content">
            {!hasKnowledge ? (
              <div className="section-empty">No knowledge stored. Click + to add one.</div>
            ) : (
              <div className="knowledge-list">
                {data.knowledge.map((item, index) => (
                  <div key={index} className="knowledge-item">
                    <div className="knowledge-header">
                      <span className="knowledge-topic">{item.topic}</span>
                      <span className="knowledge-source">{item.source}</span>
                    </div>
                    <div className="knowledge-content">{truncateText(item.content, 200)}</div>
                    <div className="knowledge-time">{formatTimestamp(item.created_at)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryPage;
