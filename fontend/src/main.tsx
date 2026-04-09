import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { preloadCriticalRoute, preloadSecondaryRoutes } from './app/routes/route-preload';
import './shared/styles/index.css';

await preloadCriticalRoute(window.location.pathname);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

void preloadSecondaryRoutes();
