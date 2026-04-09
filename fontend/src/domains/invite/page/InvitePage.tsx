import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { FollowupChat, JudgeResultCard, mediationApi } from '@/domains/mediation';
import { EventStatus } from '@/shared/api/types';
import { getErrorMessage } from '@/shared/lib';
import { DeviceFrame } from '@/shared/layout';
import { Button, Card, LoadingSpinner, Textarea } from '@/shared/ui';

export function InvitePage() {
  const navigate = useNavigate();
  const { eventId = '' } = useParams();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [showDisagreeForm, setShowDisagreeForm] = useState(false);
  const [summary, setSummary] = useState('');
  const [pointsAText, setPointsAText] = useState('');
  const [pointsBText, setPointsBText] = useState('');
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

  const commitBMutation = useMutation({
    mutationFn: () =>
      mediationApi.commitB(eventId, {
        summary: summary.trim(),
        pointsA: toBulletList(pointsAText),
        pointsB: toBulletList(pointsBText),
      }),
    onSuccess: () => setResultReady(true),
  });

  const judgeQuery = useQuery({
    queryKey: ['invite-judge-result', eventId],
    queryFn: () => mediationApi.getJudgeResult(eventId),
    enabled:
      !!eventId &&
      isAuthenticated &&
      (resultReady || inviteQuery.data?.status === EventStatus.judged),
  });

  const canSubmitDisagreement = useMemo(
    () => Boolean(summary.trim() && toBulletList(pointsAText).length > 0 && toBulletList(pointsBText).length > 0),
    [pointsAText, pointsBText, summary],
  );

  return (
    <DeviceFrame className="items-stretch">
      <div className="flex h-full w-full flex-col bg-milk-50">
        <div className="bg-milk-200 px-6 pb-12 pt-16">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Invite</p>
          <h1 className="mt-2 text-3xl font-extrabold text-coffee-900">事件邀请页</h1>
          <p className="mt-4 text-sm leading-7 text-coffee-800/70">
            先展示公开邀请信息，登录后再读取 Snapshot_A 并完成 B 的选择。
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
                  事件 ID：{inviteQuery.data.eventId} · 当前状态：{inviteQuery.data.status}
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

          {isAuthenticated && snapshotQuery.data ? (
            <>
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
                  <Button fullWidth variant="secondary" onClick={() => setShowDisagreeForm((value) => !value)}>
                    我有不同看法
                  </Button>
                </div>
                {agreeMutation.error ? (
                  <p className="text-sm font-semibold text-red-400">{getErrorMessage(agreeMutation.error)}</p>
                ) : null}
              </Card>

              {showDisagreeForm ? (
                <Card className="space-y-4">
                  <h3 className="text-lg font-extrabold text-coffee-900">提交 Snapshot_B</h3>
                  <Textarea rows={4} label="我的总结" value={summary} onChange={(event) => setSummary(event.target.value)} />
                  <Textarea
                    rows={4}
                    label="我理解 A 的重点（一行一个）"
                    value={pointsAText}
                    onChange={(event) => setPointsAText(event.target.value)}
                  />
                  <Textarea
                    rows={4}
                    label="我自己的重点（一行一个）"
                    value={pointsBText}
                    onChange={(event) => setPointsBText(event.target.value)}
                  />
                  {commitBMutation.error ? (
                    <p className="text-sm font-semibold text-red-400">{getErrorMessage(commitBMutation.error)}</p>
                  ) : null}
                  <Button
                    fullWidth
                    disabled={!canSubmitDisagreement || commitBMutation.isPending}
                    onClick={() => void commitBMutation.mutateAsync()}
                  >
                    {commitBMutation.isPending ? <LoadingSpinner /> : '提交并生成裁判结果'}
                  </Button>
                </Card>
              ) : null}
            </>
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

function toBulletList(value: string) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}
