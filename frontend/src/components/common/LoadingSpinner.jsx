import './LoadingSpinner.css';

/**
 * Loading Spinner Component
 */
function LoadingSpinner({ size = 'medium', text = '' }) {
  return (
    <div className={`loading-spinner loading-spinner-${size}`}>
      <div className="spinner"></div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
}

export default LoadingSpinner;
