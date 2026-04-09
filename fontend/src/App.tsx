import { AppProviders } from './app/providers';
import { AppRouter } from './app/router';
import { MessageViewport } from './shared/ui';

function App() {
  return (
    <AppProviders>
      <MessageViewport />
      <AppRouter />
    </AppProviders>
  );
}

export default App;
