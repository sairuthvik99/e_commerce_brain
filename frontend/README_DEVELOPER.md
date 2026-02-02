# STEB's Frontend - Developer Guide

## Technical Documentation

This guide provides comprehensive documentation for developers working on the STEB's frontend application.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Architecture](#architecture)
6. [Components](#components)
7. [State Management](#state-management)
8. [API Integration](#api-integration)
9. [Theming System](#theming-system)
10. [Testing](#testing)
11. [Deployment](#deployment)

---

## 📁 Project Overview

STEB's is a React-based frontend for an AI-powered e-commerce operations analysis platform. It provides:
- Real-time dashboard with analytics and charts
- Chat interface for AI agent interactions
- Multiple UI themes with dark/light mode support
- WebSocket support for real-time updates

---

## 🛠 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI Framework |
| Vite | 7.x | Build Tool |
| React Router DOM | 7.x | Client-side Routing |
| Recharts | 2.x | Charts & Visualization |
| CSS Variables | - | Theming System |

**No additional CSS frameworks** - Uses vanilla CSS for styling with CSS custom properties for theming.

---

## 📂 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable components
│   │   ├── chat/          # Chat-related components
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   └── QuestionCards.jsx
│   │   ├── common/        # Generic UI components
│   │   │   ├── Button.jsx
│   │   │   ├── Card.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   ├── dashboard/     # Dashboard components
│   │   │   ├── Charts.jsx
│   │   │   ├── RecentJobs.jsx
│   │   │   ├── ServiceHealth.jsx
│   │   │   └── StatCard.jsx
│   │   └── layout/        # Layout components
│   │       ├── Layout.jsx
│   │       └── Navbar.jsx
│   ├── config/            # Configuration files
│   │   └── api.js         # API endpoints config
│   ├── constants/         # Constants & static data
│   │   ├── errorMessages.js
│   │   └── questions.js
│   ├── context/           # React Context providers
│   │   ├── ChatContext.jsx
│   │   └── ThemeContext.jsx
│   ├── pages/             # Page components
│   │   ├── AgentPage/
│   │   └── HomePage/
│   ├── services/          # API & WebSocket services
│   │   ├── api.js
│   │   └── websocket.js
│   ├── styles/            # Global styles & themes
│   │   ├── global.css
│   │   └── themes.css
│   ├── App.jsx            # Root component
│   └── main.jsx           # Entry point
├── .env.example           # Environment template
├── index.html             # HTML template
├── package.json           # Dependencies
└── vite.config.js         # Vite configuration
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

### Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server on port 3000 |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

---

## 🏗 Architecture

### Component Hierarchy

```
App
├── ThemeProvider (Context)
│   └── ChatProvider (Context)
│       └── BrowserRouter
│           └── Routes
│               └── Layout
│                   ├── Navbar
│                   └── Outlet
│                       ├── HomePage
│                       └── AgentPage
```

### Data Flow

1. **User Input** → ChatContext → API Service → Backend
2. **Backend Response** → API Service → ChatContext → Components
3. **Theme Changes** → ThemeContext → CSS Variables → All Components

---

## 🧩 Components

### Layout Components

#### `Layout.jsx`
- Wraps all pages with Navbar and main content area
- Uses React Router's `Outlet` for page rendering

#### `Navbar.jsx`
- Navigation links (Home, Agent)
- UI variant selector dropdown
- Dark/light mode toggle
- Session refresh button

### Chat Components

#### `ChatInput.jsx`
- Message input textarea
- Send button (when not loading)
- Stop button (when loading)
- Keyboard shortcuts (Enter to send)

#### `ChatMessage.jsx`
- Renders user and assistant messages
- Loading animation for pending messages
- Basic markdown rendering
- Status badges (completed, failed, cancelled)

#### `QuestionCards.jsx`
- Category selection cards
- Modal with predefined questions
- Click-to-send functionality

### Dashboard Components

#### `StatCard.jsx`
- Single statistic display
- Optional icon and change indicator
- Skeleton loading state

#### `Charts.jsx`
- `JobStatusChart` - Pie chart of job statuses
- `JobsTimelineChart` - Bar chart of jobs over time
- `AgentPerformanceChart` - Horizontal bar chart

#### `RecentJobs.jsx`
- List of recent analysis jobs
- Status badges
- Empty state handling

#### `ServiceHealth.jsx`
- Backend service status display
- Latency information
- Overall health indicator

---

## 🔄 State Management

### ThemeContext

Manages UI appearance:

```jsx
const { 
  uiVariant,      // 'stebs' | 'claude' | 'twitter'
  setUiVariant,
  themeMode,      // 'light' | 'dark'
  toggleThemeMode,
  isDarkMode
} = useTheme();
```

**Features:**
- Persists to localStorage
- Applies CSS classes to document root
- Detects system preference for initial dark mode

### ChatContext

Manages chat state:

```jsx
const {
  messages,          // Array of message objects
  isLoading,         // Boolean
  currentJobId,      // String or null
  jobStatus,         // 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  jobProgress,       // Progress object or null
  sendMessage,       // Function(question)
  clearSession,      // Function()
  cancelCurrentJob   // Function()
} = useChat();
```

**Features:**
- In-memory message storage
- Automatic job status polling
- Job cancellation support

---

## 🔌 API Integration

### API Service (`services/api.js`)

Singleton class for HTTP requests:

```javascript
import { apiService } from './services/api';

// Health
await apiService.getHealth();

// Analysis
await apiService.submitAnalysis(question, context);

// Jobs
await apiService.getJobs(status, limit, page);
await apiService.getJob(jobId);
await apiService.cancelJob(jobId);
await apiService.getDashboardStats();
```

### WebSocket Service (`services/websocket.js`)

For real-time updates:

```javascript
import { wsService } from './services/websocket';

// Connect to job updates
wsService.connectToJob(jobId, (data) => {
  console.log('Update:', data);
});

// Disconnect
wsService.disconnect(jobId);
```

### API Endpoints Configuration

All endpoints are defined in `config/api.js`:

```javascript
ENDPOINTS: {
  HEALTH: '/health',
  ANALYZE: '/analyze',
  JOBS: '/jobs',
  DASHBOARD_STATS: '/dashboard/stats',
  // ... more endpoints
}
```

---

## 🎨 Theming System

### CSS Variables

All colors and styles use CSS custom properties defined in `styles/themes.css`.

### Theme Structure

Each theme variant (stebs, claude, twitter) defines:
- Primary colors
- Background colors
- Text colors
- Border colors
- Status colors (success, warning, danger, info)

### Adding a New Theme

1. Add variant to `UI_VARIANTS` in `ThemeContext.jsx`:
```javascript
export const UI_VARIANTS = {
  // ... existing
  NEW_THEME: 'new-theme'
};
```

2. Add CSS variables in `themes.css`:
```css
:root[data-ui="new-theme"][data-theme="light"],
:root.ui-new-theme.theme-light {
  --primary-color: #...;
  /* ... other variables */
}
```

3. Add option to Navbar dropdown

### Dark Mode Implementation

- Uses `data-theme` attribute on `<html>`
- Each theme has both light and dark variants
- System preference detection on initial load

---

## 🧪 Testing

### Running Tests

```bash
npm run test        # Run unit tests
npm run test:e2e    # Run end-to-end tests
```

### Component Testing Guidelines

1. Test user interactions
2. Test loading states
3. Test error states
4. Test with different themes

---

## 📦 Deployment

### Building for Production

```bash
npm run build
```

Output is in the `dist/` directory.

### Environment Configuration

For production, set `VITE_API_URL` to your production API endpoint.

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔧 Development Guidelines

### Code Style

- Use functional components with hooks
- Keep components small and focused
- Use CSS modules or component-specific CSS files
- Follow React naming conventions (PascalCase for components)

### Adding New Features

1. Create component in appropriate directory
2. Add CSS file alongside component
3. Export from directory's index.js
4. Add routes if needed
5. Update documentation

### Performance Considerations

- Use React.memo() for expensive renders
- Lazy load pages with React.lazy()
- Debounce API calls where appropriate
- Use proper key props in lists

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [React Router Documentation](https://reactrouter.com/)
- [Recharts Documentation](https://recharts.org/)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

---

*Happy coding! 🚀*
