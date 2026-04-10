import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2, Send } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { FollowupChat, JudgeResultCard, mediationApi } from '@/domains/mediation';
import type { AnalysisSessionMessagePayload } from '@/shared/api/types';
import { EventStatus } from '@/shared/api/types';
import { getErrorMessage } from '@/shared/lib';
import { DeviceFrame } from '@/shared/layout';
import { Button, Card, LoadingSpinner } from '@/shared/ui';

/**
 * InvitePage — B 侧邀请页
 *
 * B 的两种选择：
 *   1. 同意 → bAgree → 直接生成裁判
 *   2. 不同意 → startBAnalysisSession → 多轮对话 → commitAnalysisSession
 *      → 后端自动创建 Snapshot_B → judge → judged
 */
export function InvitePage() {
  const navigate = useNavigate();
  const { eventId = '' } = useParams();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  /* ── B 侧分析会话状态 ── */
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [inputText, setInputText] = useState('');
  const [canCommit, setCanCommit] = useState(false);
  const [factSummary, setFactSummary] = useState<string | null>(null);
  const [resultReady, setResultReady] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /* ── 查询邀请信息 ── */
  const inviteQuery = useQuery({
    queryKey: ['invite', eventId],
    queryFn: () => mediationApi.getInvite(eventId),
    enabled: !!eventId,
  });

  /* ── 查询 Snapshot_A ── */
  const snapshotQuery = useQuery({
    queryKey: ['snapshot-a', eventId],
    queryFn: () => mediationApi.getSnapshotA(eventId),
    enabled: isAuthenticated && !!eventId,
  });

  /* ── B 同意 ── */
  const agreeMutation = useMutation({
    mutationFn: () => mediationApi.bAgree(eventId, { agree: true }),
    onSuccess: () => setResultReady(true),
  });

  /* ── B 开启分析会话 ── */
  const startBSessionMutation = useMutation({
    mutationFn: () => mediationApi.startBAnalysisSession(eventId),
    onSuccess: (data) => {
      setSessionId(data.sessionId);
      setMessages(data.messages);
      setCanCommit(data.canCommit);
      setFactSummary(data.factSummary);
    },
  });

  /* ── B 发消息 ── */
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

  /* ── B Commit 分析会话 ── */
  const commitBSessionMutation = useMutation({
    mutationFn: () => mediationApi.commitAnalysisSession(sessionId!),
    onSuccess: () => {
      setResultReady(true);
      setSessionId(null);
    },
  });

  /* ── 查询裁判结果 ── */
  const judgeQuery = useQuery({
    queryKey: ['invite-judge-result', eventId],
    queryFn: () => mediationApi.getJudgeResult(eventId),
    enabled:
      !!eventId &&
      isAuthenticated &&
      (resultReady || inviteQuery.data?.status === EventStatus.judged),
  });

  const handleSend = () => {
    const text = inputText.trim();
    if (!text || !sessionId || sendMessageMutation.isPending) return;
    void sendMessageMutation.mutateAsync(text);
  };

  const isInBAnalysis = sessionId !== null;

  return (
    <DeviceFrame className="items-stretch">
      <div className="flex h-full w-full flex-col bg-milk-50">
        <div className="bg-milk-200 px-6 pb-12 pt-16">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Invite</p>
          <h1 className="mt-2 text-3xl font-extrabold text-coffee-900">事件邀请页</h1>
          <p className="mt-4 text-sm leading-7 text-coffee-800/70">
            {isInBAnalysis
              ? '正在和 AI 整理你的看法...'
              : '先展示公开邀请信息，登录后再读取 Snapshot_A 并完成 B 的选择。'}
          </p>
        </div>

        <div className="-mt-8 flex-1 space-y-4 overflow-y-auto px-6 pb-8">
          {/* ── 邀请信息卡片 ── */}
          <Card className="space-y-3">
            {inviteQuery.isLoading ? <p className="text-sm text-coffee-800/60">正在读取邀请信息...</p> : null}
            {inviteQuery.data ? (
              <>
                <h2 className="text-xl font-extrabold text-coffee-900">{inviteQuery.data.title ?? '未命名事件'}</h2>
                <p className="text-sm leading-7 text-coffee-800/70">{inviteQuery.data.inviteMessage}</p>
                <div className="rounded-2xl bg-milk-50 px-4 py-3 text-xs text-coffee-800/60">
                  事件 ID：{inviteQuery.data.eventId} · 当前状态：{inviteQuery.data.status}
                </div>
              </>
            ) : null}
            {inviteQuery.error ? (
              <p className="text-sm font-semibold text-red-400">{getErrorMessage(inviteQuery.error)}</p>
            ) : null}
          </Card>

          {/* ── 未登录：引导登录/注册 ── */}
          {!isAuthenticated ? (
            <Card className="space-y-4">
              <p className="text-sm leading-7 text-coffee-800/70">
                你需要先登录或注册，才能继续查看对方冻结的事实快照。
              </p>
              <div className="flex gap-3">
                <Button
                  fullWidth
                  onClick={() => navigate('/login', { state: { from: `/invite/${eventId}` } })}
                >
                  去登录
                </Button>
                <Button
                  fullWidth
                  variant="secondary"
                  onClick={() => navigate('/register', { state: { from: `/invite/${eventId}` } })}
                >
                  去注册
                </Button>
              </div>
            </Card>
          ) : null}

          {/* ── 已登录 + 快照已加载 + 还没进入 B 分析 ── */}
          {isAuthenticated && snapshotQuery.data && !isInBAnalysis && !judgeQuery.data ? (
            <Card className="space-y-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-accent-pink" />
                <h3 className="text-lg font-extrabold text-coffee-900">Snapshot_A 预览</h3>
              </div>
              <div className="rounded-3xl bg-milk-50 p-4 text-sm leading-7 text-coffee-800">
                {snapshotQuery.data.snapshotA.summary}
              </div>
              <InsightList title="A 的观点" items={snapshotQuery.data.snapshotA.pointsA} />
              <InsightList title="A 认为 B 的观点" items={snapshotQuery.data.snapshotA.pointsB} />
              <div className="flex gap-3">
                <Button fullWidth disabled={agreeMutation.isPending} onClick={() => void agreeMutation.mutateAsync()}>
                  {agreeMutation.isPending ? <LoadingSpinner /> : '我同意，生成裁判结果'}
                </Button>
                <Button
                  fullWidth
                  variant="secondary"
                  disabled={startBSessionMutation.isPending}
                  onClick={() => void startBSessionMutation.mutateAsync()}
                >
                  {startBSessionMutation.isPending ? <LoadingSpinner /> : '我有不同看法'}
                </Button>
              </div>
              {agreeMutation.error ? (
                <p className="text-sm font-semibold text-red-400">{getErrorMessage(agreeMutation.error)}</p>
              ) : null}
              {startBSessionMutation.error ? (
                <p className="text-sm font-semibold text-red-400">{getErrorMessage(startBSessionMutation.error)}</p>
              ) : null}
            </Card>
          ) : null}

          {/* ── B 侧分析会话对话界面 ── */}
          {isInBAnalysis ? (
            <>
              <Card className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
                    🤖
                  </div>
                  <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
                    你好，我来帮你整理你对这件事的看法。告诉我你认为发生了什么，以及你的想法。
                  </div>
                </div>

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
                <div ref={chatEndRef} />
              </Card>

              {/* ── 输入栏 ── */}
              <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
                <input
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-coffee-800 outline-none placeholder:text-coffee-800/40"
                  placeholder="跟 AI 说说你的看法..."
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

              {/* ── Commit 提示 ── */}
              {canCommit && factSummary ? (
                <Card className="space-y-3 border-accent-pink/30 bg-accent-pink/5">
                  <div className="flex items-center gap-2 text-coffee-900">
                    <CheckCircle2 className="h-4 w-4 text-accent-pink" />
                    <span className="text-sm font-bold">AI 认为你的看法已整理清楚，可以提交了</span>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3 text-sm leading-7 text-coffee-800">
                    <p className="mb-1 text-xs font-bold text-coffee-800/40">事实摘要</p>
                    {factSummary}
                  </div>
                  {commitBSessionMutation.error ? (
                    <p className="text-sm font-semibold text-red-400">{getErrorMessage(commitBSessionMutation.error)}</p>
                  ) : null}
                  <Button
                    fullWidth
                    disabled={commitBSessionMutation.isPending}
                    onClick={() => void commitBSessionMutation.mutateAsync()}
                  >
                    {commitBSessionMutation.isPending ? <LoadingSpinner /> : '提交并生成裁判结果'}
                  </Button>
                </Card>
              ) : null}
            </>
          ) : null}

          {/* ── 裁判结果 ── */}
          {judgeQuery.data ? (
            <>
              <JudgeResultCard result={judgeQuery.data} />
              <FollowupChat eventId={eventId} />
              <Button fullWidth variant="secondary" onClick={() => navigate('/app/mediation')}>
                去调解室继续查看
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </>
          ) : null}

          {snapshotQuery.isLoading ? <p className="text-sm text-coffee-800/60">正在加载快照内容...</p> : null}
          {judgeQuery.error ? <p className="text-sm font-semibold text-red-400">{getErrorMessage(judgeQuery.error)}</p> : null}

          <p className="pb-6 text-center text-sm text-coffee-800/60">
            <Link className="font-bold text-coffee-900" to="/app/home">
              返回主页
            </Link>
          </p>
        </div>
      </div>
    </DeviceFrame>
  );
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-3xl border border-milk-100 bg-white px-4 py-3">
      <p className="text-sm font-bold text-coffee-900">{title}</p>
      <ul className="mt-2 space-y-2 text-sm text-coffee-800/80">
        {items.length > 0 ? items.map((item) => <li key={item}>• {item}</li>) : <li>• 暂无内容</li>}
      </ul>
    </div>
  );
}
