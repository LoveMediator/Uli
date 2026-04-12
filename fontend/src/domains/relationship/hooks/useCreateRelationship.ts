import { useMutation } from '@tanstack/react-query';
import { createRelationshipInvite, acceptRelationshipInvite } from '@/domains/relationship/api/relationship';

const useCreateRelationship = () => {
  const createInvite = useMutation({
    mutationFn: createRelationshipInvite,
  });

  const acceptInvite = useMutation({
    mutationFn: (inviteCode: string) => acceptRelationshipInvite(inviteCode),
  });

  return {
    createInvite,
    acceptInvite,
  };
};

export { useCreateRelationship };