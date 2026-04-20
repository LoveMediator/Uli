import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, CheckCircle2, Copy, Heart, MessageCircle, RefreshCcw, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { mediationApi } from '@/domains/mediation/api/mediation-api';
import { useCurrentEvent } from '@/domains/mediation/model/use-current-event';
import { AnalysisChatPanel } from '@/domains/mediation/ui/AnalysisChatPanel';
import { FollowupChat } from '@/domains/mediation/ui/FollowupChat';
import { JudgeResultCard } from '@/domains/mediation/ui/JudgeResultCard';
import type { AnalysisSessionMessagePayload } from '@/shared/api/types';
import { EventStatus, type EventStatusValue } from '@/shared/api/types';
import { formatEventStatus, getErrorMessage } from '@/shared/lib';
import { Button, Card, Input, LoadingSpinner, pushMessage } from '@/shared/ui';

export function MediationPage() {
  const judgeVisibleStatuses = new Set<EventStatusValue>([
    EventStatus.judged,
    EventStatus.reviewed,
    EventStatus.closed,
  ]);
  const navigate = useNavigate();
  const { currentEvent, relationshipId, setCurrentEvent, patchCurrentEvent, clearCurrentEvent } =
    useCurrentEvent();
  const publicId = useAuthStore((state) => state.publicId);
  const eventStatusLabel = formatEventStatus(currentEvent?.status);
  const hasRelationship = relationshipId.trim().length > 0;
  const canViewJudge = !!currentEvent && judgeVisibleStatuses.has(currentEvent.status);

  const [sessionId, setSessionId] = useState<string | null>(currentEvent?.sessionId ?? null);
  const [sessionInitialMessages, setSessionInitialMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [sessionInitialCanCommit, setSessionInitialCanCommit] = useState(false);
  const [sessionInitialFactSummary, setSessionInitialFactSummary] = useState<string | null>(null);

  const [relayTargetUserId, setRelayTargetUserId] = useState('');
  const [relayMessage, setRelayMessage] = useState('');
  const [relayResult, setRelayResult] = useState('');

  const startSessionMutation = useMutation({
    mutationFn: () => mediationApi.startAAnalysisSession(relationshipId),
    onSuccess: (data) => {
      setSessionId(data.sessionId);
      setSessionInitialMessages(data.messages);
      setSessionInitialCanCommit(data.canCommit);
      setSessionInitialFactSummary(data.factSummary);
    },
  });

  const judgeQuery = useQuery({
    queryKey: ['judge-result', currentEvent?.eventId],
    queryFn: () => mediationApi.getJudgeResult(currentEvent!.eventId),
    enabled: canViewJudge,
  });

  const handleRefreshJudge = async () => {
    try {
      const result = await judgeQuery.refetch();
      if (result.data) {
        patchCurrentEvent({ status: result.data.status });
      }
    } catch {
      // Error content is already rendered from judgeQuery.error.
    }
  };

  const relayMutation = useMutation({
    mutationFn: () =>
      mediationApi.relayMessage({
        eventId: currentEvent!.eventId,
        targetUserId: relayTargetUserId.trim(),
        rawMessage: relayMessage.trim(),
      }),
    onSuccess: (data) => {
      setRelayResult(data.finalMessage);
      setRelayMessage('');
    },
  });

  const inviteLink = currentEvent ? `${window.location.origin}/invite/${currentEvent.eventId}` : '';

  const handleCopyInviteLink = async () => {
    if (!inviteLink) {
      return;
    }

    try {
      await navigator.clipboard.writeText(inviteLink);
      pushMessage({
        tone: 'success',
        text: '邀请链接已复制。',
      });
    } catch {
      pushMessage({
        tone: 'warning',
        text: '复制失败，请手动复制下方邀请链接。',
      });
    }
  };

  const isInAnalysisPhase = sessionId !== null && !currentEvent;

  return (
    <div className="relative flex h-full flex-col bg-milk-50">
      <header className="flex items-center justify-between border-b border-milk-100 bg-white/80 px-6 pb-4 pt-14 shadow-sm backdrop-blur">
        <div>
          <h1 className="text-xl font-bold text-coffee-900">AI 调解室</h1>
          <p className="text-[11px] font-medium text-coffee-800/50">
            {isInAnalysisPhase ? '正在和 AI 一起梳理事实...' : '让 AI 先帮你把冲突事实整理清楚'}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-milk-200 bg-milk-100">
          <Bot className="h-5 w-5 text-coffee-800" />
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-40 pt-4">
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 text-xs font-bold text-coffee-900 shadow-sm">
            AI
          </div>
          <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
            你好，我会帮你把这次冲突整理成可确认的事实。点下面的“开始分析”，先告诉我发生了什么。
          </div>
        </div>

        {currentEvent ? (
          <Card className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Current Event</p>
                <h2 className="mt-1 text-lg font-extrabold text-coffee-900">{currentEvent.title}</h2>
                <p className="mt-1 text-xs text-coffee-800/60">事件 ID：{currentEvent.eventId}</p>
              </div>
              <span className="rounded-full bg-milk-100 px-3 py-1 text-xs font-bold text-coffee-900">
                {eventStatusLabel}
              </span>
            </div>

            {currentEvent.status === EventStatus.waitingB ? (
              <div className="space-y-3 rounded-3xl bg-milk-50 p-4">
                <div className="flex items-center gap-2 text-coffee-900">
                  <CheckCircle2 className="h-4 w-4 text-accent-pink" />
                  <span className="text-sm font-bold">Snapshot_A 已冻结，正在等待对方处理</span>
                </div>
                <div className="rounded-2xl border border-milk-200 bg-white px-4 py-3 text-sm text-coffee-800">
                  <p className="font-semibold">邀请链接</p>
                  <p className="mt-2 break-all text-xs leading-6">{inviteLink}</p>
                </div>
                <div className="flex gap-3">
                  <Button fullWidth variant="secondary" onClick={() => void handleCopyInviteLink()}>
                    <Copy className="mr-2 h-4 w-4" />
                    复制链接
                  </Button>
                  <Button fullWidth variant="ghost" onClick={() => void handleRefreshJudge()}>
                    {judgeQuery.isFetching ? <LoadingSpinner /> : <RefreshCcw className="mr-2 h-4 w-4" />}
                    检查结果
                  </Button>
                </div>
                {judgeQuery.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(judgeQuery.error)}</p> : null}
              </div>
            ) : null}

            {canViewJudge && judgeQuery.data ? (
              <>
                <JudgeResultCard result={judgeQuery.data} />
                <FollowupChat eventId={currentEvent.eventId} />
              </>
            ) : null}

            {currentEvent.status !== EventStatus.draft ? (
              <div className="space-y-3 rounded-3xl border border-milk-100 bg-white px-4 py-4">
                <div className="flex items-center gap-2">
                  <Heart className="h-4 w-4 text-accent-pink" />
                  <span className="text-sm font-bold text-coffee-900">小精灵代转达</span>
                </div>
                <p className="text-xs leading-6 text-coffee-800/60">
                  当前后端还没有关系成员信息查询，这里先手动填写对方的 publicId。
                </p>
                <Input
                  placeholder="对方 publicId，例如 u_seed_b_1"
                  value={relayTargetUserId}
                  onChange={(event) => setRelayTargetUserId(event.target.value)}
                />
                <textarea
                  rows={3}
                  className="w-full rounded-2xl border border-milk-200 bg-milk-50 px-4 py-3 text-sm text-coffee-800 outline-none focus:border-coffee-300"
                  placeholder="想让小精灵帮你润色并转达的话"
                  value={relayMessage}
                  onChange={(event) => setRelayMessage(event.target.value)}
                />
                <Button
                  fullWidth
                  disabled={!relayTargetUserId.trim() || !relayMessage.trim() || relayMutation.isPending}
                  onClick={() => void relayMutation.mutateAsync()}
                >
                  {relayMutation.isPending ? <LoadingSpinner /> : '发送代转达'}
                </Button>
                {relayResult ? (
                  <div className="rounded-2xl bg-milk-50 px-4 py-3 text-sm leading-7 text-coffee-800">{relayResult}</div>
                ) : null}
                {relayMutation.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(relayMutation.error)}</p> : null}
              </div>
            ) : null}

            <Button variant="secondary" fullWidth onClick={clearCurrentEvent}>
              清空当前事件
            </Button>
          </Card>
        ) : isInAnalysisPhase ? (
          <AnalysisChatPanel
            key={sessionId}
            sessionId={sessionId}
            initialMessages={sessionInitialMessages}
            initialCanCommit={sessionInitialCanCommit}
            initialFactSummary={sessionInitialFactSummary}
            commitLabel="确认提交，并邀请对方参与"
            inputPlaceholder="和 AI 说说发生了什么..."
            onCommitted={(data) => {
              setCurrentEvent({
                eventId: data.eventId,
                title: '分析已提交',
                status: data.status,
                sessionId: sessionId ?? undefined,
                snapshotAId: data.snapshotAId ?? undefined,
              });
              setSessionId(null);
            }}
          />
        ) : (
          <Card className="space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">开始分析</p>
              <h2 className="mt-2 text-xl font-extrabold text-coffee-900">发起一件新的冲突事件</h2>
              <p className="mt-2 text-sm leading-6 text-coffee-800/70">
                {hasRelationship
                  ? '你可以先和 AI 说说发生了什么，AI 会帮你整理事实，然后再邀请对方参与。'
                  : '先绑定一段关系，再开始新的调解事件。'}
              </p>
            </div>
            {startSessionMutation.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(startSessionMutation.error)}</p> : null}
            {hasRelationship ? (
              <Button fullWidth disabled={startSessionMutation.isPending} onClick={() => void startSessionMutation.mutateAsync()}>
                {startSessionMutation.isPending ? <LoadingSpinner /> : '开始分析'}
              </Button>
            ) : (
              <Button fullWidth onClick={() => navigate('/app/relationship')}>
                去绑定关系
              </Button>
            )}
          </Card>
        )}

        {publicId ? (
          <div className="rounded-3xl bg-white/80 px-4 py-3 text-xs leading-6 text-coffee-800/60 shadow-soft">
            当前用户 publicId：{publicId}
          </div>
        ) : null}
      </div>

      {!isInAnalysisPhase ? (
        <div className="absolute bottom-[85px] left-0 right-0 z-20 px-4">
          <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
            <div className="rounded-full bg-milk-100 p-2 text-coffee-800">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="flex-1 text-sm text-coffee-800/60">
              {currentEvent ? '当前事件已经建立，可以继续推进流程。' : '先开始分析，和 AI 说说到底发生了什么。'}
            </div>
            <MessageCircle className="h-5 w-5 text-coffee-800/40" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
