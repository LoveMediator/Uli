import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, CheckCircle2, Copy, Heart, MessageCircle, RefreshCcw, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/domains/auth';
import { mediationApi } from '@/domains/mediation/api/mediation-api';
import { useCurrentEvent } from '@/domains/mediation/model/use-current-event';
import { AnalysisChatPanel } from '@/domains/mediation/ui/AnalysisChatPanel';
import { FollowupChat } from '@/domains/mediation/ui/FollowupChat';
import { JudgeResultCard } from '@/domains/mediation/ui/JudgeResultCard';
import type { AnalysisSessionMessagePayload } from '@/shared/api/types';
import { EventStatus } from '@/shared/api/types';
import { getErrorMessage } from '@/shared/lib';
import { Button, Card, Input, LoadingSpinner } from '@/shared/ui';

/**
 * MediationPage — A 侧调解室
 *
 * 新流程：
 *   1. 点击「开始分析」→ startAAnalysisSession(relationshipId)
 *   2. 与 AI 多轮对话    → sendAnalysisMessage(sessionId, { message })
 *   3. AI 返回 canCommit=true 后显示 commit 按钮
 *   4. 点击 commit       → commitAnalysisSession(sessionId)
 *      → 后端自动创建 Event + Snapshot_A → waiting_b
 */
export function MediationPage() {
  const { currentEvent, relationshipId, setCurrentEvent, patchCurrentEvent, clearCurrentEvent } =
    useCurrentEvent();
  const publicId = useAuthStore((state) => state.publicId);

  /* ── 分析会话状态 ── */
  const [sessionId, setSessionId] = useState<string | null>(currentEvent?.sessionId ?? null);
  const [sessionInitialMessages, setSessionInitialMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [sessionInitialCanCommit, setSessionInitialCanCommit] = useState(false);
  const [sessionInitialFactSummary, setSessionInitialFactSummary] = useState<string | null>(null);

  /* ── 小精灵转达 ── */
  const [relayTargetUserId, setRelayTargetUserId] = useState('');
  const [relayMessage, setRelayMessage] = useState('');
  const [relayResult, setRelayResult] = useState('');

  /* ── 开启 A 侧分析会话 ── */
  const startSessionMutation = useMutation({
    mutationFn: () => mediationApi.startAAnalysisSession(relationshipId),
    onSuccess: (data) => {
      setSessionId(data.sessionId);
      setSessionInitialMessages(data.messages);
      setSessionInitialCanCommit(data.canCommit);
      setSessionInitialFactSummary(data.factSummary);
    },
  });

  /* ── 查询裁判结果（#6 修复：改用 useQuery + refetch） ── */
  const judgeQuery = useQuery({
    queryKey: ['judge-result', currentEvent?.eventId],
    queryFn: () => mediationApi.getJudgeResult(currentEvent!.eventId),
    enabled: !!currentEvent && currentEvent.status === EventStatus.judged,
  });

  /* ── 手动刷新裁判结果 ── */
  const handleRefreshJudge = async () => {
    try {
      const result = await judgeQuery.refetch();
      if (result.data) {
        patchCurrentEvent({ status: EventStatus.judged });
      }
    } catch {
      // error 由 judgeQuery.error 展示
    }
  };

  /* ── 小精灵代转达 ── */
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

  /* ── 分析会话已开启但还没 commit ── */
  const isInAnalysisPhase = sessionId !== null && !currentEvent;

  return (
    <div className="relative flex h-full flex-col bg-milk-50">
      <header className="flex items-center justify-between border-b border-milk-100 bg-white/80 px-6 pb-4 pt-14 shadow-sm backdrop-blur">
        <div>
          <h1 className="text-xl font-bold text-coffee-900">AI 调解室</h1>
          <p className="text-[11px] font-medium text-coffee-800/50">
            {isInAnalysisPhase ? '正在和 AI 整理事实...' : '让 AI 帮你梳理争吵事实'}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-milk-200 bg-milk-100">
          <Bot className="h-5 w-5 text-coffee-800" />
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-40 pt-4">
        {/* ── 欢迎消息 ── */}
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
            🤖
          </div>
          <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
            你好呀，我会帮你把这次冲突整理成可确认的事实。点击下方「开始分析」，跟我聊聊发生了什么。
          </div>
        </div>

        {/* ── 已有事件 ── */}
        {currentEvent ? (
          <Card className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Current Event</p>
                <h2 className="mt-1 text-lg font-extrabold text-coffee-900">{currentEvent.title}</h2>
                <p className="mt-1 text-xs text-coffee-800/60">事件 ID：{currentEvent.eventId}</p>
              </div>
              <span className="rounded-full bg-milk-100 px-3 py-1 text-xs font-bold text-coffee-900">
                {currentEvent.status}
              </span>
            </div>

            {currentEvent.status === EventStatus.waitingB ? (
              <div className="space-y-3 rounded-3xl bg-milk-50 p-4">
                <div className="flex items-center gap-2 text-coffee-900">
                  <CheckCircle2 className="h-4 w-4 text-accent-pink" />
                  <span className="text-sm font-bold">Snapshot_A 已冻结，正在等待 B 处理</span>
                </div>
                <div className="rounded-2xl border border-milk-200 bg-white px-4 py-3 text-sm text-coffee-800">
                  <p className="font-semibold">邀请链接</p>
                  <p className="mt-2 break-all text-xs leading-6">{inviteLink}</p>
                </div>
                <div className="flex gap-3">
                  <Button
                    fullWidth
                    variant="secondary"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(inviteLink);
                      } catch {
                        window.alert(inviteLink);
                      }
                    }}
                  >
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

            {currentEvent.status === EventStatus.judged && judgeQuery.data ? (
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
                  当前后端没有关系成员信息查询，所以这里先手动填写对方 `publicId`。
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
          /* ── 分析会话对话界面 ── */
          <AnalysisChatPanel
            sessionId={sessionId}
            initialMessages={sessionInitialMessages}
            initialCanCommit={sessionInitialCanCommit}
            initialFactSummary={sessionInitialFactSummary}
            commitLabel="确认提交，邀请对方参与"
            inputPlaceholder="跟 AI 说说发生了什么..."
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
          /* ── 初始：开始分析按钮 ── */
          <Card className="space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">开始分析</p>
              <h2 className="mt-2 text-xl font-extrabold text-coffee-900">发起一件新的冲突事件</h2>
              <p className="mt-2 text-sm leading-6 text-coffee-800/70">
                你可以跟 AI 倾诉发生了什么事，AI 会帮你把事实整理清楚，然后邀请对方参与。
              </p>
            </div>
            {startSessionMutation.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(startSessionMutation.error)}</p> : null}
            <Button
              fullWidth
              disabled={startSessionMutation.isPending}
              onClick={() => void startSessionMutation.mutateAsync()}
            >
              {startSessionMutation.isPending ? <LoadingSpinner /> : '开始分析'}
            </Button>
          </Card>
        )}

        {publicId ? (
          <div className="rounded-3xl bg-white/80 px-4 py-3 text-xs leading-6 text-coffee-800/60 shadow-soft">
            当前用户 publicId：{publicId}
          </div>
        ) : null}
      </div>

      {/* ── 底部提示栏（非分析阶段） ── */}
      {!isInAnalysisPhase ? (
        <div className="absolute bottom-[85px] left-0 right-0 z-20 px-4">
          <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
            <div className="rounded-full bg-milk-100 p-2 text-coffee-800">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="flex-1 text-sm text-coffee-800/60">
              {currentEvent ? '当前事件已就绪，可以继续推进流程。' : '先开始分析，跟 AI 聊聊发生了什么。'}
            </div>
            <MessageCircle className="h-5 w-5 text-coffee-800/40" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
