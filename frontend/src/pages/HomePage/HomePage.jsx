import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../../services/api';
import { LoadingSpinner } from '../../components/common';
import { 
  StatCard, 
  JobStatusChart, 
  JobsTimelineChart,
  AgentPerformanceChart,
  RecentJobs,
  ServiceHealth 
} from '../../components/dashboard';
import './HomePage.css';

/**
 * Home Page - Dashboard
 * Displays statistics, charts, and service health
 */
function HomePage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [dashboard, health] = await Promise.all([
        apiService.getDashboardStats(),
        apiService.getHealth()
      ]);
      
      setDashboardData(dashboard);
      setHealthData(health);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="home-page loading">
        <LoadingSpinner size="large" text="Loading dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="home-page error">
        <div className="error-container">
          <span className="error-icon">⚠️</span>
          <h2>Unable to Load Dashboard</h2>
          <p>{error}</p>
          <button className="retry-button" onClick={fetchData}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const summary = dashboardData?.summary || {};
  const hasEcommerceData = summary.total_revenue !== undefined;

  // Format currency
  const formatCurrency = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className="home-page">
      <div className="home-container">
        {/* Header */}
        <header className="home-header">
          <div className="header-content">
            <h1>Dashboard</h1>
            <p>E-Commerce Operations Analytics</p>
            {summary.data_range && (
              <span className="data-range">
                Data: {summary.data_range.start} to {summary.data_range.end}
              </span>
            )}
          </div>
          <button className="refresh-button" onClick={fetchData}>
            🔄 Refresh
          </button>
        </header>

        {/* E-Commerce Stats Grid */}
        {hasEcommerceData ? (
          <section className="stats-grid">
            <StatCard 
              label="Total Revenue"
              value={formatCurrency(summary.total_revenue || 0)}
              icon="💰"
              changeType="positive"
            />
            <StatCard 
              label="Yesterday Revenue"
              value={formatCurrency(summary.yesterday_revenue || 0)}
              icon="📈"
            />
            <StatCard 
              label="Total Orders"
              value={(summary.total_orders || 0).toLocaleString()}
              icon="🛒"
            />
            <StatCard 
              label="Avg Order Value"
              value={formatCurrency(summary.avg_order_value || 0)}
              icon="💳"
            />
          </section>
        ) : (
          <section className="stats-grid">
            <StatCard 
              label="Total Analyses"
              value={summary.total_jobs || 0}
              icon="📊"
            />
            <StatCard 
              label="Last 24 Hours"
              value={summary.jobs_last_24h || 0}
              icon="⏰"
            />
            <StatCard 
              label="Success Rate"
              value={`${summary.success_rate || 0}%`}
              icon="✅"
              changeType={summary.success_rate >= 80 ? 'positive' : summary.success_rate >= 50 ? 'neutral' : 'negative'}
            />
            <StatCard 
              label="Avg. Time"
              value={`${(summary.avg_completion_time_seconds || 0).toFixed(1)}s`}
              icon="⚡"
            />
          </section>
        )}

        {/* Secondary Stats Row for E-Commerce */}
        {hasEcommerceData && (
          <section className="stats-grid secondary">
            <StatCard 
              label="Stockouts"
              value={summary.total_stockouts || 0}
              icon="📦"
              changeType={summary.total_stockouts > 10 ? 'negative' : 'neutral'}
            />
            <StatCard 
              label="Stockout Products"
              value={summary.stockout_products || 0}
              icon="⚠️"
              changeType={summary.stockout_products > 5 ? 'negative' : 'neutral'}
            />
            <StatCard 
              label="Complaints"
              value={summary.total_complaints || 0}
              icon="🎧"
              changeType={summary.total_complaints > 50 ? 'negative' : 'neutral'}
            />
            <StatCard 
              label="Marketing ROI"
              value={summary.marketing_spend ? 
                `${((summary.marketing_conversions / (summary.marketing_spend / 100)) || 0).toFixed(1)}%` : 
                'N/A'
              }
              icon="📢"
            />
          </section>
        )}

        {/* Charts Row */}
        <section className="charts-row">
          <div className="chart-col">
            <JobStatusChart data={dashboardData?.by_status} />
          </div>
          <div className="chart-col">
            <JobsTimelineChart data={dashboardData?.jobs_by_hour} />
          </div>
        </section>

        {/* Bottom Row */}
        <section className="bottom-row">
          <div className="bottom-col wide">
            <AgentPerformanceChart data={dashboardData?.agent_stats} />
          </div>
          <div className="bottom-col">
            <ServiceHealth health={healthData} />
          </div>
        </section>

        {/* Recent Jobs */}
        <section className="recent-section">
          <RecentJobs jobs={dashboardData?.recent_jobs} />
        </section>
      </div>
    </div>
  );
}

export default HomePage;
