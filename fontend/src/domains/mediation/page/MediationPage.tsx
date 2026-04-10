import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, CheckCircle2, Copy, Heart, MessageCircle, RefreshCcw, Send, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/domains/auth';
import { mediationApi } from '@/domains/mediation/api/mediation-api';
import { useCurrentEvent } from '@/domains/mediation/model/use-current-event';
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
  const [messages, setMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [inputText, setInputText] = useState('');
  const [canCommit, setCanCommit] = useState(false);
  const [factSummary, setFactSummary] = useState<string | null>(null);

  /* ── 小精灵转达 ── */
  const [relayTargetUserId, setRelayTargetUserId] = useState('');
  const [relayMessage, setRelayMessage] = useState('');
  const [relayResult, setRelayResult] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /* ── 开启 A 侧分析会话 ── */
  const startSessionMutation = useMutation({
    mutationFn: () => mediationApi.startAAnalysisSession(relationshipId),
    onSuccess: (data) => {
      setSessionId(data.sessionId);
      setMessages(data.messages);
      setCanCommit(data.canCommit);
      setFactSummary(data.factSummary);
    },
  });

  /* ── 发消息 ── */
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      mediationApi.sendAnalysisMessage(sessionId!, { message }),
    onSuccess: (data, sentMessage) => {
      const now = new Date().toISOString();
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: sentMessage, createdAt: now, images: [] },
        { role: 'assistant', content: data.reply, createdAt: now, images: [] },
      ]);
      setCanCommit(data.canCommit);
      setFactSummary(data.factSummary);
      setInputText('');
    },
  });

  /* ── Commit 分析会话 ── */
  const commitSessionMutation = useMutation({
    mutationFn: () => mediationApi.commitAnalysisSession(sessionId!),
    onSuccess: (data) => {
      setCurrentEvent({
        eventId: data.eventId,
        title: factSummary ?? '分析已提交',
        status: data.status,
        sessionId: sessionId ?? undefined,
        snapshotAId: data.snapshotAId ?? undefined,
      });
      setSessionId(null);
      setMessages([]);
      setCanCommit(false);
      setFactSummary(null);
    },
  });

  /* ── 查询裁判结果 ── */
  const judgeQuery = useQuery({
    queryKey: ['judge-result', currentEvent?.eventId],
    queryFn: () => mediationApi.getJudgeResult(currentEvent!.eventId),
    enabled: currentEvent?.status === EventStatus.judged,
  });

  /* ── 查看裁判结果（A 等待 B 处理时手动刷新） ── */
  const refreshJudgeMutation = useMutation({
    mutationFn: () => mediationApi.getJudgeResult(currentEvent!.eventId),
    onSuccess: () => {
      patchCurrentEvent({ status: EventStatus.judged });
    },
  });

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

  const handleSend = () => {
    const text = inputText.trim();
    if (!text || !sessionId || sendMessageMutation.isPending) return;
    void sendMessageMutation.mutateAsync(text);
  };

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
                  <Button fullWidth variant="ghost" onClick={() => void refreshJudgeMutation.mutateAsync()}>
                    {refreshJudgeMutation.isPending ? <LoadingSpinner /> : <RefreshCcw className="mr-2 h-4 w-4" />}
                    检查结果
                  </Button>
                </div>
                {refreshJudgeMutation.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(refreshJudgeMutation.error)}</p> : null}
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
          <>
            {messages.map((msg, index) => (
              <div key={`${msg.role}-${index}`} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'assistant' ? (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
                    🤖
                  </div>
                ) : null}
                <div
                  className={
                    msg.role === 'assistant'
                      ? 'max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm'
                      : 'max-w-[82%] rounded-2xl rounded-tr-none bg-coffee-100 p-3.5 text-sm leading-7 text-coffee-900 shadow-sm'
                  }
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {sendMessageMutation.isPending ? (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
                  🤖
                </div>
                <div className="flex items-center gap-2 rounded-2xl rounded-tl-none border border-milk-50 bg-white px-4 py-3 shadow-sm">
                  <LoadingSpinner />
                  <span className="text-sm text-coffee-800/60">AI 正在思考...</span>
                </div>
              </div>
            ) : null}

            {canCommit && factSummary ? (
              <Card className="space-y-3 border-accent-pink/30 bg-accent-pink/5">
                <div className="flex items-center gap-2 text-coffee-900">
                  <CheckCircle2 className="h-4 w-4 text-accent-pink" />
                  <span className="text-sm font-bold">AI 认为事实已整理清楚，可以提交了</span>
                </div>
                <div className="rounded-2xl bg-white px-4 py-3 text-sm leading-7 text-coffee-800">
                  <p className="mb-1 text-xs font-bold text-coffee-800/40">事实摘要</p>
                  {factSummary}
                </div>
                {commitSessionMutation.error ? (
                  <p className="text-sm font-semibold text-red-400">{getErrorMessage(commitSessionMutation.error)}</p>
                ) : null}
                <Button
                  fullWidth
                  disabled={commitSessionMutation.isPending}
                  onClick={() => void commitSessionMutation.mutateAsync()}
                >
                  {commitSessionMutation.isPending ? <LoadingSpinner /> : '确认提交，邀请对方参与'}
                </Button>
              </Card>
            ) : null}
            <div ref={chatEndRef} />
          </>

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

      {/* ── 底部输入栏（分析阶段可见） ── */}
      {isInAnalysisPhase ? (
        <div className="absolute bottom-[85px] left-0 right-0 z-20 px-4">
          <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
            <input
              className="flex-1 bg-transparent px-3 py-2 text-sm text-coffee-800 outline-none placeholder:text-coffee-800/40"
              placeholder="跟 AI 说说发生了什么..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={sendMessageMutation.isPending}
            />
            <button
              className="flex h-10 w-10 items-center justify-center rounded-full bg-coffee-800 text-white transition-colors hover:bg-coffee-900 disabled:opacity-40"
              disabled={!inputText.trim() || sendMessageMutation.isPending}
              onClick={handleSend}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : (
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
      )}
    </div>
  );
}
