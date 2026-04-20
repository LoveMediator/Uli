import { QueryClientProvider } from '@tanstack/react-query';
import { type PropsWithChildren, useState } from 'react';
import { createAppQueryClient } from '@/app/providers/create-query-client';
import { RelationshipBootstrap } from '@/domains/relationship/model/RelationshipBootstrap';

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(() => createAppQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <RelationshipBootstrap />
      {children}
    </QueryClientProvider>
  );
}
