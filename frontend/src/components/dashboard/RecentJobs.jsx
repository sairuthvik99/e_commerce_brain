import Card from '../common/Card';
import AssignmentIcon from '@mui/icons-material/Assignment';
import './RecentJobs.css';

/**
 * Recent Jobs Component
 * Displays a list of recent analysis jobs
 */
function RecentJobs({ jobs = [], loading = false }) {
  const getStatusBadge = (status) => {
    const badges = {
      completed: { text: 'Completed', class: 'badge-success' },
      running: { text: 'Running', class: 'badge-info' },
      pending: { text: 'Pending', class: 'badge-warning' },
      failed: { text: 'Failed', class: 'badge-danger' },
      cancelled: { text: 'Cancelled', class: 'badge-secondary' }
    };
    return badges[status] || { text: status, class: 'badge-secondary' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card className="recent-jobs-card">
        <h3 className="recent-jobs-title">Recent Analyses</h3>
        <div className="recent-jobs-skeleton">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton-row">
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-badge"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="recent-jobs-card">
      <h3 className="recent-jobs-title">Recent Analyses</h3>
      
      {jobs.length === 0 ? (
        <div className="recent-jobs-empty">
          <AssignmentIcon className="empty-icon" sx={{ fontSize: 40 }} />
          <p>No analyses yet</p>
        </div>
      ) : (
        <div className="recent-jobs-list">
          {jobs.map(job => {
            const badge = getStatusBadge(job.status);
            return (
              <div key={job.job_id} className="recent-job-item">
                <div className="job-info">
                  <span className="job-question">{job.question}</span>
                  <span className="job-time">{formatDate(job.created_at)}</span>
                </div>
                <span className={`job-badge ${badge.class}`}>
                  {badge.text}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

export default RecentJobs;
