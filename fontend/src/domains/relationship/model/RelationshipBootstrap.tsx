import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '@/app/model/app-store';
import { useAuthStore } from '@/domains/auth';
import { getRelationships } from '@/domains/relationship/api/relationship';

export function RelationshipBootstrap() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const relationshipId = useAppStore((state) => state.relationshipId);
  const currentEvent = useAppStore((state) => state.currentEvent);
  const setRelationshipId = useAppStore((state) => state.setRelationshipId);
  const clearCurrentEvent = useAppStore((state) => state.clearCurrentEvent);

  const relationshipsQuery = useQuery({
    queryKey: ['relationships'],
    queryFn: getRelationships,
    enabled: isAuthenticated,
    staleTime: 60_000,
  });

  useEffect(() => {
    if (!isAuthenticated || !relationshipsQuery.data) {
      return;
    }

    const items = relationshipsQuery.data.items;
    const nextRelationshipId = items[0]?.relationshipId ?? '';
    const hasCurrentRelationship = items.some((item) => item.relationshipId === relationshipId);

    if (hasCurrentRelationship) {
      return;
    }

    if (relationshipId !== nextRelationshipId) {
      setRelationshipId(nextRelationshipId);
    }

    if (currentEvent) {
      clearCurrentEvent();
    }
  }, [
    clearCurrentEvent,
    currentEvent,
    isAuthenticated,
    relationshipId,
    relationshipsQuery.data,
    setRelationshipId,
  ]);

  return null;
}
