import Card from '../common/Card';
import './StatCard.css';

/**
 * Stat Card Component
 * Displays a single statistic with label and optional change indicator
 */
function StatCard({ 
  label, 
  value, 
  icon = null, 
  change = null, 
  changeType = 'neutral',
  loading = false 
}) {
  return (
    <Card className="stat-card">
      {loading ? (
        <div className="stat-card-skeleton">
          <div className="skeleton skeleton-icon"></div>
          <div className="skeleton skeleton-value"></div>
          <div className="skeleton skeleton-label"></div>
        </div>
      ) : (
        <>
          <div className="stat-card-header">
            {icon && <span className="stat-icon">{icon}</span>}
            {change !== null && (
              <span className={`stat-change stat-change-${changeType}`}>
                {changeType === 'positive' && '↑'}
                {changeType === 'negative' && '↓'}
                {change}%
              </span>
            )}
          </div>
          <div className="stat-value">{value}</div>
          <div className="stat-label">{label}</div>
        </>
      )}
    </Card>
  );
}

export default StatCard;
