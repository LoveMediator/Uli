import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { FollowupChat, JudgeResultCard, mediationApi } from '@/domains/mediation';
import { AnalysisChatPanel } from '@/domains/mediation/ui/AnalysisChatPanel';
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
  const [sessionInitialMessages, setSessionInitialMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [sessionInitialCanCommit, setSessionInitialCanCommit] = useState(false);
  const [sessionInitialFactSummary, setSessionInitialFactSummary] = useState<string | null>(null);
  const [resultReady, setResultReady] = useState(false);

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
      setSessionInitialMessages(data.messages);
      setSessionInitialCanCommit(data.canCommit);
      setSessionInitialFactSummary(data.factSummary);
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
            <Card className="space-y-3">
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
                  🤖
                </div>
                <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
                  你好，我来帮你整理你对这件事的看法。告诉我你认为发生了什么，以及你的想法。
                </div>
              </div>

              <AnalysisChatPanel
                sessionId={sessionId}
                initialMessages={sessionInitialMessages}
                initialCanCommit={sessionInitialCanCommit}
                initialFactSummary={sessionInitialFactSummary}
                commitLabel="提交并生成裁判结果"
                inputPlaceholder="跟 AI 说说你的看法..."
                onCommitted={() => {
                  setResultReady(true);
                  setSessionId(null);
                }}
              />
            </Card>
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
