import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from 'recharts';
import Card from '../common/Card';
import { useTheme } from '../../context/ThemeContext';
import './Charts.css';

// Chart colors
const COLORS = {
  primary: '#6366f1',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  secondary: '#8b5cf6'
};

const STATUS_COLORS = {
  completed: COLORS.success,
  running: COLORS.info,
  pending: COLORS.warning,
  failed: COLORS.danger,
  cancelled: COLORS.secondary
};

/**
 * Job Status Pie Chart
 */
export function JobStatusChart({ data, loading = false }) {
  const { isDarkMode } = useTheme();
  
  if (loading) {
    return (
      <Card className="chart-card">
        <div className="chart-skeleton"></div>
      </Card>
    );
  }

  const chartData = Object.entries(data || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: STATUS_COLORS[name] || COLORS.secondary
  }));

  return (
    <Card className="chart-card">
      <h3 className="chart-title">Jobs by Status</h3>
      <div className="chart-container pie-chart">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={50}
              paddingAngle={2}
              label={({ name, value }) => `${name}: ${value}`}
              labelLine={false}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                background: isDarkMode ? '#1f2937' : '#fff',
                border: '1px solid',
                borderColor: isDarkMode ? '#374151' : '#e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

/**
 * Jobs Over Time Chart
 */
export function JobsTimelineChart({ data, loading = false }) {
  const { isDarkMode } = useTheme();
  
  if (loading) {
    return (
      <Card className="chart-card">
        <div className="chart-skeleton"></div>
      </Card>
    );
  }

  const chartData = Object.entries(data || {})
    .map(([hour, count]) => ({
      hour,
      jobs: count
    }))
    .reverse();

  return (
    <Card className="chart-card">
      <h3 className="chart-title">Jobs (Last 24 Hours)</h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={isDarkMode ? '#374151' : '#e5e7eb'}
            />
            <XAxis 
              dataKey="hour" 
              tick={{ fill: isDarkMode ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              tickLine={false}
            />
            <YAxis 
              tick={{ fill: isDarkMode ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: isDarkMode ? '#1f2937' : '#fff',
                border: '1px solid',
                borderColor: isDarkMode ? '#374151' : '#e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Bar 
              dataKey="jobs" 
              fill={COLORS.primary} 
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

/**
 * Agent Performance Chart
 */
export function AgentPerformanceChart({ data, loading = false }) {
  const { isDarkMode } = useTheme();
  
  if (loading) {
    return (
      <Card className="chart-card">
        <div className="chart-skeleton"></div>
      </Card>
    );
  }

  const chartData = Object.entries(data || {}).map(([agent, stats]) => ({
    agent: agent.charAt(0).toUpperCase() + agent.slice(1),
    invocations: stats.count || 0,
    findings: stats.has_findings || 0
  }));

  return (
    <Card className="chart-card">
      <h3 className="chart-title">Agent Performance</h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={isDarkMode ? '#374151' : '#e5e7eb'}
            />
            <XAxis 
              type="number"
              tick={{ fill: isDarkMode ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              tickLine={false}
            />
            <YAxis 
              type="category"
              dataKey="agent"
              tick={{ fill: isDarkMode ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                background: isDarkMode ? '#1f2937' : '#fff',
                border: '1px solid',
                borderColor: isDarkMode ? '#374151' : '#e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar 
              dataKey="invocations" 
              fill={COLORS.primary} 
              radius={[0, 4, 4, 0]}
              name="Invocations"
            />
            <Bar 
              dataKey="findings" 
              fill={COLORS.success} 
              radius={[0, 4, 4, 0]}
              name="With Findings"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export default {
  JobStatusChart,
  JobsTimelineChart,
  AgentPerformanceChart
};
