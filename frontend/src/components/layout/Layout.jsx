import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import './Layout.css';

/**
 * Layout Component
 * Wraps all pages with navbar and common structure
 */
function Layout() {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
