import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '@/app/model/app-store';
import { useAuthStore } from '@/domains/auth';
import { getRelationships } from '@/domains/relationship/api/relationship';
import type { CurrentEventSession } from '@/domains/mediation';
import type { RelationshipSummary } from '@/shared/api/types';

function mapCurrentEvent(relationship: RelationshipSummary): CurrentEventSession | null {
  if (!relationship.currentEvent) {
    return null;
  }

  return {
    eventId: relationship.currentEvent.eventId,
    title: relationship.currentEvent.title ?? '未命名事件',
    status: relationship.currentEvent.status,
    pendingAction: relationship.currentEvent.pendingAction,
    relationshipId: relationship.relationshipId,
    partnerUserId: relationship.partnerUserId,
    partnerUsername: relationship.partnerUsername,
  };
}

function isSameEvent(left: CurrentEventSession | null, right: CurrentEventSession | null) {
  if (!left || !right) {
    return left === right;
  }

  return (
    left.eventId === right.eventId &&
    left.title === right.title &&
    left.status === right.status &&
    left.pendingAction === right.pendingAction &&
    left.relationshipId === right.relationshipId &&
    left.partnerUserId === right.partnerUserId &&
    left.partnerUsername === right.partnerUsername
  );
}

function isSameRelationship(left: RelationshipSummary | null, right: RelationshipSummary | null) {
  if (!left || !right) {
    return left === right;
  }

  return (
    left.relationshipId === right.relationshipId &&
    left.partnerUserId === right.partnerUserId &&
    left.partnerUsername === right.partnerUsername &&
    left.status === right.status &&
    left.currentEvent?.eventId === right.currentEvent?.eventId &&
    left.currentEvent?.status === right.currentEvent?.status &&
    left.currentEvent?.pendingAction === right.currentEvent?.pendingAction &&
    left.currentEvent?.title === right.currentEvent?.title
  );
}

export function RelationshipBootstrap() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const relationshipId = useAppStore((state) => state.relationshipId);
  const activeRelationship = useAppStore((state) => state.activeRelationship);
  const currentEvent = useAppStore((state) => state.currentEvent);
  const setRelationshipId = useAppStore((state) => state.setRelationshipId);
  const setActiveRelationship = useAppStore((state) => state.setActiveRelationship);
  const setCurrentEvent = useAppStore((state) => state.setCurrentEvent);
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
    const selectedRelationship =
      items.find((item) => item.relationshipId === relationshipId) ?? items[0] ?? null;

    if (!selectedRelationship) {
      if (relationshipId) {
        setRelationshipId('');
      }
      if (activeRelationship) {
        setActiveRelationship(null);
      }
      if (currentEvent) {
        clearCurrentEvent();
      }
      return;
    }

    if (relationshipId !== selectedRelationship.relationshipId) {
      setRelationshipId(selectedRelationship.relationshipId);
    }

    if (!isSameRelationship(activeRelationship, selectedRelationship)) {
      setActiveRelationship(selectedRelationship);
    }

    const nextEvent = mapCurrentEvent(selectedRelationship);
    if (nextEvent && currentEvent?.eventId === nextEvent.eventId) {
      nextEvent.sessionId = currentEvent.sessionId;
      nextEvent.snapshotAId = currentEvent.snapshotAId;
      nextEvent.judgeResultId = currentEvent.judgeResultId;
    }

    if (!isSameEvent(currentEvent, nextEvent)) {
      if (nextEvent) {
        setCurrentEvent(nextEvent);
      } else {
        clearCurrentEvent();
      }
    }
  }, [
    activeRelationship,
    clearCurrentEvent,
    currentEvent,
    isAuthenticated,
    relationshipId,
    relationshipsQuery.data,
    setActiveRelationship,
    setCurrentEvent,
    setRelationshipId,
  ]);

  useEffect(() => {
    if (isAuthenticated) {
      return;
    }

    if (activeRelationship) {
      setActiveRelationship(null);
    }
    if (currentEvent) {
      clearCurrentEvent();
    }
  }, [
    activeRelationship,
    clearCurrentEvent,
    currentEvent,
    isAuthenticated,
    setActiveRelationship,
  ]);

  return null;
}
