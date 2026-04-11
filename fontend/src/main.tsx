import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { preloadCriticalRoute, preloadSecondaryRoutes } from './app/routes/route-preload';
import './shared/styles/index.css';

const currentPathname = window.location.pathname;

await preloadCriticalRoute(currentPathname);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

preloadSecondaryRoutes(currentPathname);
