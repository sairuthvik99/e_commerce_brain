import { NavLink } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import { useChat } from '../../context/ChatContext';
import { ModelSelector } from '../common';
import PsychologyIcon from '@mui/icons-material/Psychology';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import RefreshIcon from '@mui/icons-material/Refresh';
import './Navbar.css';

/**
 * Navbar Component
 * Contains navigation links, theme toggle, model selector, and refresh button
 */
function Navbar() {
  const { toggleThemeMode, isDarkMode } = useTheme();
  const { clearSession } = useChat();

  const handleRefresh = () => {
    if (window.confirm('This will clear your current chat session. Continue?')) {
      clearSession();
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo / Brand */}
        <div className="navbar-brand">
          <NavLink to="/" className="brand-link">
            <PsychologyIcon className="brand-icon" sx={{ fontSize: 28 }} />
            <span className="brand-text">STEB's</span>
          </NavLink>
        </div>

        {/* Navigation Links */}
        <div className="navbar-nav">
          <NavLink 
            to="/" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <DashboardIcon className="nav-icon" sx={{ fontSize: 20 }} />
            <span className="nav-text">Home</span>
          </NavLink>
          
          <NavLink 
            to="/agent" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <SmartToyIcon className="nav-icon" sx={{ fontSize: 20 }} />
            <span className="nav-text">Agent</span>
          </NavLink>
        </div>

        {/* Right side controls */}
        <div className="navbar-controls">
          {/* LLM Model Selector */}
          <ModelSelector />

          {/* Theme Toggle */}
          <button 
            className="theme-toggle"
            onClick={toggleThemeMode}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
          >
            {isDarkMode ? <LightModeIcon sx={{ fontSize: 20 }} /> : <DarkModeIcon sx={{ fontSize: 20 }} />}
          </button>

          {/* Refresh Button */}
          <button 
            className="refresh-button"
            onClick={handleRefresh}
            title="Clear chat session"
            aria-label="Refresh session"
          >
            <RefreshIcon sx={{ fontSize: 20 }} />
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
