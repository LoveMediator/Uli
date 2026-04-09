import { homeApi, moderateMessage } from '@/domains/home';
import { relayMessage } from '@/domains/mediation';

export { moderateMessage, relayMessage };

export const elfApi = {
  moderateMessage,
  relayMessage,
};

export { homeApi };
