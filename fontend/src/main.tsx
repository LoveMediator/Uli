import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { preloadCriticalRoute, preloadSecondaryRoutes } from './app/routes/route-preload';
import './shared/styles/index.css';

const currentPathname = window.location.pathname;

async function bootstrap() {
  try {
    await preloadCriticalRoute(currentPathname);
  } catch (error) {
    // Never block app bootstrap on route preloading errors.
    console.error('Failed to preload critical route, continuing bootstrap.', error);
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );

  try {
    preloadSecondaryRoutes(currentPathname);
  } catch (error) {
    console.error('Failed to schedule secondary route preloads.', error);
  }
}

void bootstrap();
