import './Button.css';

/**
 * Button Component
 * Reusable button with variants
 */
function Button({ 
  children, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  loading = false,
  className = '',
  ...props 
}) {
  return (
    <button 
      className={`btn btn-${variant} btn-${size} ${loading ? 'btn-loading' : ''} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="btn-spinner"></span>}
      <span className={loading ? 'btn-text-hidden' : ''}>{children}</span>
    </button>
  );
}

export default Button;
