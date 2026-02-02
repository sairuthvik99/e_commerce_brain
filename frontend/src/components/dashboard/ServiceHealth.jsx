import Card from '../common/Card';
import './ServiceHealth.css';

/**
 * Service Health Component
 * Displays health status of backend services
 */
function ServiceHealth({ health = null, loading = false }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'unhealthy':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const formatLatency = (latency) => {
    if (latency === null || latency === undefined) return '-';
    return `${latency.toFixed(0)}ms`;
  };

  if (loading) {
    return (
      <Card className="service-health-card">
        <h3 className="service-health-title">System Health</h3>
        <div className="service-health-skeleton">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton-service">
              <div className="skeleton skeleton-icon"></div>
              <div className="skeleton skeleton-name"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  const services = health?.services || {};

  return (
    <Card className="service-health-card">
      <div className="service-health-header">
        <h3 className="service-health-title">System Health</h3>
        <span className={`overall-status status-${health?.status || 'unknown'}`}>
          {getStatusIcon(health?.status)} {health?.status || 'Unknown'}
        </span>
      </div>

      <div className="service-list">
        {Object.entries(services).map(([name, service]) => (
          <div key={name} className="service-item">
            <div className="service-main">
              <span className="service-status-icon">
                {getStatusIcon(service.status)}
              </span>
              <span className="service-name">
                {name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
              </span>
            </div>
            <div className="service-details">
              <span className="service-latency">
                {formatLatency(service.latency_ms)}
              </span>
              {service.message && (
                <span className="service-message" title={service.message}>
                  {service.message.length > 30 
                    ? `${service.message.substring(0, 30)}...` 
                    : service.message}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {health?.version && (
        <div className="service-health-footer">
          <span className="version-label">API Version: {health.version}</span>
        </div>
      )}
    </Card>
  );
}

export default ServiceHealth;
