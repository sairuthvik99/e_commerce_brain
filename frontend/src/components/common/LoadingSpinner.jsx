import './LoadingSpinner.css';

/**
 * Loading Spinner Component
 * Supports multiple variants: spinner, pulse, dots, dashboard
 */
function LoadingSpinner({ size = 'medium', text = '', variant = 'spinner' }) {
  if (variant === 'dashboard') {
    return (
      <div className="dashboard-loader">
        <div className="loader-content">
          <div className="loader-brain">
            <div className="brain-core"></div>
            <div className="brain-ring ring-1"></div>
            <div className="brain-ring ring-2"></div>
            <div className="brain-ring ring-3"></div>
            <div className="brain-pulse"></div>
          </div>
          <div className="loader-text-container">
            <h3 className="loader-title">Loading Dashboard</h3>
            <p className="loader-subtitle">{text || 'Fetching your data...'}</p>
            <div className="loader-progress">
              <div className="progress-bar"></div>
            </div>
          </div>
          <div className="loader-stats">
            <div className="stat-skeleton"></div>
            <div className="stat-skeleton"></div>
            <div className="stat-skeleton"></div>
            <div className="stat-skeleton"></div>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'dots') {
    return (
      <div className={`loading-spinner loading-spinner-${size}`}>
        <div className="dots-container">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
        {text && <p className="loading-text">{text}</p>}
      </div>
    );
  }

  if (variant === 'pulse') {
    return (
      <div className={`loading-spinner loading-spinner-${size}`}>
        <div className="pulse-container">
          <div className="pulse-ring"></div>
          <div className="pulse-core"></div>
        </div>
        {text && <p className="loading-text">{text}</p>}
      </div>
    );
  }

  return (
    <div className={`loading-spinner loading-spinner-${size}`}>
      <div className="spinner"></div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
}

export default LoadingSpinner;
