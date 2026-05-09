import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bell, MessageCircle, Send } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/app/model/app-store';
import { useAuthStore } from '@/domains/auth';
import { homeApi } from '@/domains/home/api/home-api';
import { useHomeOverlay } from '@/domains/home/model/use-home-overlay';
import { mediationApi } from '@/domains/mediation';
import { formatEventStatus, getErrorMessage } from '@/shared/lib';
import { Button, LoadingSpinner, Modal, Textarea } from '@/shared/ui';

export function HomePage() {
  const navigate = useNavigate();
  const username = useAuthStore((state) => state.usernameDraft) || '小红薯';
  const relationshipId = useAppStore((state) => state.relationshipId);
  const activeRelationship = useAppStore((state) => state.activeRelationship);
  const currentEvent = useAppStore((state) => state.currentEvent);
  const currentRelationshipId = activeRelationship?.relationshipId || relationshipId;
  const hasRelationship = currentRelationshipId.trim().length > 0;
  const partnerName = activeRelationship?.partnerUsername ?? '对方';
  const relayTargetUserId = currentEvent?.partnerUserId ?? activeRelationship?.partnerUserId ?? '';
  const canRelay = !!currentEvent && !!relayTargetUserId;
  const quickStartTitle = currentEvent ? '当前调解正在进行' : '准备开始一次新的调解';
  const quickStartCopy = currentEvent
    ? `和 ${partnerName} 的事件状态：${formatEventStatus(currentEvent.status)}`
    : hasRelationship
      ? `当前关系：${partnerName}`
      : '你还没有绑定关系，先去邀请或加入一段关系吧。';
  const quickStartButtonLabel = currentEvent ? '查看调解状态' : hasRelationship ? '进入调解室' : '去绑定关系';
  const { homeOverlayOpen, setHomeOverlayOpen } = useHomeOverlay();
  const [message, setMessage] = useState('');
  const [petReply, setPetReply] = useState('');

  const elfMessagesQuery = useQuery({
    queryKey: ['elf-messages'],
    queryFn: () => homeApi.getElfMessages(5),
    staleTime: 30_000,
  });

  const latestIncoming = elfMessagesQuery.data?.items[0];
  const petBubbleText =
    petReply ||
    (latestIncoming
      ? `${latestIncoming.fromUsername} 通过小精灵转达：${latestIncoming.finalMessage}`
      : '点我一下，把不好开口的话先告诉我。');

  const moderateMutation = useMutation({
    mutationFn: homeApi.moderateMessage,
    onSuccess: (data) => {
      setPetReply(data.suggestedMessage || '这句话已经很温和了，可以直接发给对方。');
      setHomeOverlayOpen(false);
      setMessage('');
    },
  });

  const relayMutation = useMutation({
    mutationFn: (rawMessage: string) =>
      mediationApi.relayMessage({
        eventId: currentEvent!.eventId,
        targetUserId: relayTargetUserId,
        rawMessage,
      }),
    onSuccess: (data) => {
      setPetReply(`已帮你转达给${partnerName}：${data.finalMessage}`);
      void elfMessagesQuery.refetch();
      setHomeOverlayOpen(false);
      setMessage('');
    },
  });

  const isSubmitting = moderateMutation.isPending || relayMutation.isPending;
  const formError = relayMutation.error ?? moderateMutation.error;

  return (
    <div className="relative flex h-full flex-col bg-milk-50">
      <div className="pointer-events-none absolute inset-0 z-0 flex flex-col">
        <div className="relative h-[65%] w-full bg-stripe-pattern">
          <div className="absolute right-8 top-24 h-24 w-20 overflow-hidden rounded-lg border-4 border-white bg-blue-50 shadow-inner">
            <div className="h-1/2 w-full border-b-4 border-white bg-blue-100" />
            <div className="absolute left-1/2 top-0 h-full w-1 bg-white" />
          </div>
        </div>
        <div className="relative h-[35%] w-full overflow-hidden bg-milk-200">
          <div className="floor-perspective absolute inset-0 bg-grid-pattern bg-[length:40px_40px] opacity-30" />
          <div className="absolute bottom-24 left-1/2 h-12 w-48 -translate-x-1/2 rounded-[50%] bg-black/5 blur-sm" />
        </div>
      </div>

      <header className="relative z-20 flex items-center justify-between px-6 pt-14">
        <div 
          className="cursor-pointer flex items-center gap-2 rounded-full border border-white bg-white/90 px-3 py-1.5 shadow-sm backdrop-blur hover:bg-white/95 transition-colors"
          onClick={() => navigate('/app/relationship')}
        >
          <div className="flex -space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-accent-pink text-xs font-bold text-white">
              A
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-accent-blue text-xs font-bold text-white">
              B
            </div>
          </div>
          <span className="text-xs font-bold text-coffee-800">Love &amp; Peace</span>
        </div>
        <button type="button" className="relative flex h-10 w-10 items-center justify-center rounded-full bg-white/90 shadow-sm">
          <Bell className="h-5 w-5 text-coffee-800" />
          <span className="absolute right-2.5 top-2 h-2 w-2 rounded-full border border-white bg-red-400" />
        </button>
      </header>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-end pb-32">
        <div className="mb-5 rounded-full border border-milk-200 bg-white/95 px-5 py-2 shadow-sm">
          <p className="text-sm font-bold text-coffee-900">{username} 的小精灵</p>
        </div>

        <button
          type="button"
          className="group relative transition-transform active:scale-95"
          onClick={() => setHomeOverlayOpen(true)}
        >
          <div className="relative z-10 flex h-44 w-44 items-center justify-center rounded-[4rem] border-4 border-white bg-gradient-to-br from-accent-pink via-milk-300 to-accent-blue text-5xl font-black text-coffee-900 shadow-float animate-float">
            AI
          </div>
          <div className="absolute -right-10 -top-14 rounded-2xl rounded-bl-none bg-white px-4 py-2 shadow-lg animate-wiggle">
            <p className="text-xs font-bold text-coffee-800">点我</p>
          </div>
        </button>

        <div className="mt-6 max-w-[250px] rounded-3xl bg-white/95 px-5 py-4 text-center text-sm font-semibold leading-6 text-coffee-800 shadow-soft">
          {petBubbleText}
        </div>
      </div>

      <div className="relative z-10 px-6 pb-28">
        <div className="rounded-[28px] border border-white/70 bg-white/90 p-4 shadow-soft">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-coffee-800/40">Quick Start</p>
          <h2 className="mt-2 text-xl font-extrabold text-coffee-900">{quickStartTitle}</h2>
          <p className="mt-2 text-sm leading-6 text-coffee-800/70">
            {quickStartCopy}
          </p>
          <Button fullWidth className="mt-4" onClick={() => navigate(hasRelationship ? '/app/mediation' : '/app/relationship')}>
            {quickStartButtonLabel}
          </Button>
        </div>
      </div>

      <Modal open={homeOverlayOpen} onClose={() => setHomeOverlayOpen(false)}>
        <div className="rounded-[30px] bg-white p-6 shadow-2xl">
          <h3 className="mb-2 flex items-center gap-2 text-lg font-bold text-coffee-900">
            <MessageCircle className="h-5 w-5 text-accent-pink" />
            {canRelay ? `让我帮你转达给${partnerName}` : '先让我帮你润一下语气'}
          </h3>
          <p className="mb-4 text-sm leading-6 text-coffee-800/70">
            {canRelay
              ? '我会先把表达整理得更温和，再记录为一条给对方的代转达。'
              : '当前还没有进行中的调解事件，我可以先帮你把表达整理得更温和。'}
          </p>
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              const value = message.trim();
              if (!value) {
                return;
              }
              if (canRelay) {
                void relayMutation.mutateAsync(value);
                return;
              }
              void moderateMutation.mutateAsync({ rawMessage: value });
            }}
          >
            <Textarea
              rows={4}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="比如：你为什么总是不提前说一声？"
            />
            {formError ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(formError)}</p> : null}
            <Button fullWidth type="submit" disabled={isSubmitting}>
              {isSubmitting ? <LoadingSpinner /> : <Send className="mr-2 h-4 w-4" />}
              {canRelay ? '发送代转达' : '获取温和表达'}
            </Button>
          </form>
        </div>
      </Modal>
    </div>
  );
}
