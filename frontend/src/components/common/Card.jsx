import './Card.css';

/**
 * Card Component
 * Reusable card container
 */
function Card({ 
  children, 
  className = '', 
  onClick = null, 
  hoverable = false,
  ...props 
}) {
  return (
    <div 
      className={`card ${hoverable ? 'card-hoverable' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick(e) : undefined}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
