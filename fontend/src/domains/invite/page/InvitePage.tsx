import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { FollowupChat, JudgeResultCard, mediationApi } from '@/domains/mediation';
import { AnalysisChatPanel } from '@/domains/mediation/ui/AnalysisChatPanel';
import type { AnalysisSessionMessagePayload } from '@/shared/api/types';
import { EventStatus } from '@/shared/api/types';
import { formatEventStatus, getErrorMessage } from '@/shared/lib';
import { DeviceFrame } from '@/shared/layout';
import { Button, Card, LoadingSpinner } from '@/shared/ui';

export function InvitePage() {
  const navigate = useNavigate();
  const { eventId = '' } = useParams();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionInitialMessages, setSessionInitialMessages] = useState<AnalysisSessionMessagePayload[]>([]);
  const [sessionInitialCanCommit, setSessionInitialCanCommit] = useState(false);
  const [sessionInitialFactSummary, setSessionInitialFactSummary] = useState<string | null>(null);
  const [resultReady, setResultReady] = useState(false);

  const inviteQuery = useQuery({
    queryKey: ['invite', eventId],
    queryFn: () => mediationApi.getInvite(eventId),
    enabled: !!eventId,
  });

  const snapshotQuery = useQuery({
    queryKey: ['snapshot-a', eventId],
    queryFn: () => mediationApi.getSnapshotA(eventId),
    enabled: isAuthenticated && !!eventId,
  });

  const agreeMutation = useMutation({
    mutationFn: () => mediationApi.bAgree(eventId, { agree: true }),
    onSuccess: () => setResultReady(true),
  });

  const startBSessionMutation = useMutation({
    mutationFn: () => mediationApi.startBAnalysisSession(eventId),
    onSuccess: (data) => {
      setSessionId(data.sessionId);
      setSessionInitialMessages(data.messages);
      setSessionInitialCanCommit(data.canCommit);
      setSessionInitialFactSummary(data.factSummary);
    },
  });

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
              ? '正在和 AI 一起整理你的看法...'
              : '先查看公开邀请信息，登录后再读取 Snapshot_A，并决定是否认同这次事实整理。'}
          </p>
        </div>

        <div className="-mt-8 flex-1 space-y-4 overflow-y-auto px-6 pb-8">
          <Card className="space-y-3">
            {inviteQuery.isLoading ? <p className="text-sm text-coffee-800/60">正在读取邀请信息...</p> : null}
            {inviteQuery.data ? (
              <>
                <h2 className="text-xl font-extrabold text-coffee-900">{inviteQuery.data.title ?? '未命名事件'}</h2>
                <p className="text-sm leading-7 text-coffee-800/70">{inviteQuery.data.inviteMessage}</p>
                <div className="rounded-2xl bg-milk-50 px-4 py-3 text-xs text-coffee-800/60">
                  事件 ID：{inviteQuery.data.eventId} · 当前状态：{formatEventStatus(inviteQuery.data.status)}
                </div>
              </>
            ) : null}
            {inviteQuery.error ? (
              <p className="text-sm font-semibold text-red-400">{getErrorMessage(inviteQuery.error)}</p>
            ) : null}
          </Card>

          {!isAuthenticated ? (
            <Card className="space-y-4">
              <p className="text-sm leading-7 text-coffee-800/70">
                你需要先登录或注册，才能继续查看对方冻结的事实快照。
              </p>
              <div className="flex gap-3">
                <Button fullWidth onClick={() => navigate('/login', { state: { from: `/invite/${eventId}` } })}>
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
                  {agreeMutation.isPending ? <LoadingSpinner /> : '我同意，生成裁决结果'}
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

          {isInBAnalysis ? (
            <Card className="space-y-3">
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 text-xs font-bold text-coffee-900 shadow-sm">
                  AI
                </div>
                <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
                  你好，我来帮你整理你对这件事的看法。告诉我你认为什么发生了，以及你在意的点是什么。
                </div>
              </div>

              <AnalysisChatPanel
                key={sessionId}
                sessionId={sessionId}
                initialMessages={sessionInitialMessages}
                initialCanCommit={sessionInitialCanCommit}
                initialFactSummary={sessionInitialFactSummary}
                commitLabel="提交并生成裁决结果"
                inputPlaceholder="和 AI 说说你的看法..."
                onCommitted={() => {
                  setResultReady(true);
                  setSessionId(null);
                }}
              />
            </Card>
          ) : null}

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
              返回首页
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
        {items.length > 0 ? items.map((item) => <li key={item}>· {item}</li>) : <li>暂无内容</li>}
      </ul>
    </div>
  );
}
