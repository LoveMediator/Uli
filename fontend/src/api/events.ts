import {
  bAgree,
  commitA,
  commitB,
  createEvent,
  getInvite,
  getJudgeResult,
  getSnapshotA,
  mediationApi as domainMediationApi,
  sendFollowupMessage,
} from '@/domains/mediation';

export { bAgree, commitA, commitB, createEvent, getInvite, getJudgeResult, getSnapshotA, sendFollowupMessage };

export const eventsApi = domainMediationApi;
