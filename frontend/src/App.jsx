import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ChatProvider } from './context/ChatContext';
import { ModelProvider } from './context/ModelContext';
import { Layout } from './components/layout';
import HomePage from './pages/HomePage';
import AgentPage from './pages/AgentPage';
import MemoryPage from './pages/MemoryPage';
import './styles/global.css';

/**
 * Main App Component
 * Sets up routing and global providers
 */
function App() {
  return (
    <ThemeProvider>
      <ModelProvider>
        <ChatProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="agent" element={<AgentPage />} />
                <Route path="memory" element={<MemoryPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ChatProvider>
      </ModelProvider>
    </ThemeProvider>
  );
}

export default App;
