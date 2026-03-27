import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, CheckCircle2, Copy, Heart, MessageCircle, RefreshCcw, Sparkles } from 'lucide-react';
import { elfApi, eventsApi } from '@/api';
import { FollowupChat } from '@/components/business/FollowupChat';
import { JudgeResultCard } from '@/components/business/JudgeResultCard';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { useCurrentEvent } from '@/hooks';
import { useAuthStore } from '@/stores/auth-store';
import { EventStatus } from '@/types';
import { getErrorMessage } from '@/utils';

type TempMessage = {
  role: 'user' | 'assistant';
  content: string;
};

export function MediationPage() {
  const { currentEvent, relationshipId, setCurrentEvent, patchCurrentEvent, clearCurrentEvent } =
    useCurrentEvent();
  const publicId = useAuthStore((state) => state.publicId);
  const [title, setTitle] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [analysisInputOpen, setAnalysisInputOpen] = useState(false);
  const [analysisPreviewOpen, setAnalysisPreviewOpen] = useState(false);
  const [relayTargetUserId, setRelayTargetUserId] = useState('');
  const [relayMessage, setRelayMessage] = useState('');
  const [relayResult, setRelayResult] = useState('');

  const tempMessages = useMemo<TempMessage[]>(
    () =>
      confirmText.trim()
        ? [
            { role: 'user', content: confirmText },
            {
              role: 'assistant',
              content: '我先帮你把这件事整理成可确认的事实版本。如果你觉得差不多，就可以冻结成 Snapshot_A 再邀请对方加入。',
            },
          ]
        : [],
    [confirmText],
  );

  const createEventMutation = useMutation({
    mutationFn: () => eventsApi.createEvent({ title: title.trim(), relationshipId }),
    onSuccess: (data) => {
      setCurrentEvent({
        eventId: data.eventId,
        title: title.trim(),
        status: data.status,
      });
      setTitle('');
    },
  });

  const commitMutation = useMutation({
    mutationFn: () => eventsApi.commitA(currentEvent!.eventId, { confirmText: confirmText.trim() }),
    onSuccess: (data) => {
      patchCurrentEvent({
        status: data.status,
        snapshotAId: data.snapshotAId,
      });
      setAnalysisPreviewOpen(false);
      setConfirmText('');
    },
  });

  const judgeQuery = useQuery({
    queryKey: ['judge-result', currentEvent?.eventId],
    queryFn: () => eventsApi.getJudgeResult(currentEvent!.eventId),
    enabled: currentEvent?.status === EventStatus.judged,
  });

  const refreshJudgeMutation = useMutation({
    mutationFn: () => eventsApi.getJudgeResult(currentEvent!.eventId),
    onSuccess: () => {
      patchCurrentEvent({ status: EventStatus.judged });
    },
  });

  const relayMutation = useMutation({
    mutationFn: () =>
      elfApi.relayMessage({
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

  return (
    <div className="relative flex h-full flex-col bg-milk-50">
      <header className="flex items-center justify-between border-b border-milk-100 bg-white/80 px-6 pb-4 pt-14 shadow-sm backdrop-blur">
        <div>
          <h1 className="text-xl font-bold text-coffee-900">AI 调解室</h1>
          <p className="text-[11px] font-medium text-coffee-800/50">让真实接口驱动这次完整调解闭环</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-milk-200 bg-milk-100">
          <Bot className="h-5 w-5 text-coffee-800" />
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-40 pt-4">
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 shadow-sm">
            🤖
          </div>
          <div className="max-w-[82%] rounded-2xl rounded-tl-none border border-milk-50 bg-white p-3.5 text-sm leading-7 text-coffee-800 shadow-sm">
            你好呀，我会帮你把这次冲突整理成可确认的事实，并在双方进入后展示固定的裁判结果。
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
                {currentEvent.status}
              </span>
            </div>

            {currentEvent.status === EventStatus.draft ? (
              <Button fullWidth onClick={() => setAnalysisInputOpen(true)}>
                进入争吵事件分析模式
              </Button>
            ) : null}

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
                {refreshJudgeMutation.error ? (
                  <p className="text-sm font-semibold text-red-400">
                    {getErrorMessage(refreshJudgeMutation.error)}
                  </p>
                ) : null}
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
                <Textarea
                  rows={3}
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
                  <div className="rounded-2xl bg-milk-50 px-4 py-3 text-sm leading-7 text-coffee-800">
                    {relayResult}
                  </div>
                ) : null}
                {relayMutation.error ? (
                  <p className="text-sm font-semibold text-red-400">{getErrorMessage(relayMutation.error)}</p>
                ) : null}
              </div>
            ) : null}

            <Button variant="secondary" fullWidth onClick={clearCurrentEvent}>
              清空当前事件
            </Button>
          </Card>
        ) : (
          <Card className="space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Create Event</p>
              <h2 className="mt-2 text-xl font-extrabold text-coffee-900">发起一件新的冲突事件</h2>
              <p className="mt-2 text-sm leading-6 text-coffee-800/70">会调用真实的 `POST /events`，默认关系 ID：{relationshipId}</p>
            </div>
            <Input
              label="事件标题"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="比如：昨晚关于家务分工的争执"
            />
            {createEventMutation.error ? (
              <p className="text-sm font-semibold text-red-400">{getErrorMessage(createEventMutation.error)}</p>
            ) : null}
            <Button
              fullWidth
              disabled={!title.trim() || createEventMutation.isPending}
              onClick={() => void createEventMutation.mutateAsync()}
            >
              {createEventMutation.isPending ? <LoadingSpinner /> : '创建事件'}
            </Button>
          </Card>
        )}

        {publicId ? (
          <div className="rounded-3xl bg-white/80 px-4 py-3 text-xs leading-6 text-coffee-800/60 shadow-soft">
            当前用户 publicId：{publicId}
          </div>
        ) : null}
      </div>

      <div className="absolute bottom-[85px] left-0 right-0 z-20 px-4">
        <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
          <div className="rounded-full bg-milk-100 p-2 text-coffee-800">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="flex-1 text-sm text-coffee-800/60">
            {currentEvent ? '当前事件已就绪，可以继续推进流程。' : '先创建事件，再进入分析与冻结流程。'}
          </div>
          <MessageCircle className="h-5 w-5 text-coffee-800/40" />
        </div>
      </div>

      <Modal open={analysisInputOpen} onClose={() => setAnalysisInputOpen(false)}>
        <Card className="space-y-4 rounded-[32px]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Step 1</p>
            <h3 className="mt-1 text-xl font-extrabold text-coffee-900">记录这次事件</h3>
          </div>
          <Textarea
            rows={6}
            label="确认文本"
            placeholder="请把你确认无误、愿意冻结成事实快照的内容写在这里。"
            value={confirmText}
            onChange={(event) => setConfirmText(event.target.value)}
          />
          <div className="flex gap-3">
            <Button fullWidth variant="secondary" onClick={() => setAnalysisInputOpen(false)}>
              先不写
            </Button>
            <Button
              fullWidth
              onClick={() => {
                setAnalysisInputOpen(false);
                setAnalysisPreviewOpen(true);
              }}
              disabled={!confirmText.trim()}
            >
              继续整理
            </Button>
          </div>
        </Card>
      </Modal>

      <Modal open={analysisPreviewOpen} onClose={() => setAnalysisPreviewOpen(false)}>
        <Card className="space-y-4 rounded-[32px]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Step 2</p>
            <h3 className="mt-1 text-xl font-extrabold text-coffee-900">确认并冻结 Snapshot_A</h3>
          </div>
          <div className="max-h-64 space-y-3 overflow-y-auto rounded-3xl bg-milk-50 p-4">
            {tempMessages.map((item, index) => (
              <div
                key={`${item.role}-${index}`}
                className={
                  item.role === 'assistant'
                    ? 'mr-8 rounded-3xl rounded-tl-md bg-white p-3 text-sm leading-7 text-coffee-800'
                    : 'ml-8 rounded-3xl rounded-tr-md bg-coffee-100 p-3 text-sm leading-7 text-coffee-900'
                }
              >
                {item.content}
              </div>
            ))}
          </div>
          {commitMutation.error ? (
            <p className="text-sm font-semibold text-red-400">{getErrorMessage(commitMutation.error)}</p>
          ) : null}
          <div className="flex gap-3">
            <Button
              fullWidth
              variant="secondary"
              onClick={() => {
                setAnalysisPreviewOpen(false);
                setAnalysisInputOpen(true);
              }}
            >
              继续修改
            </Button>
            <Button fullWidth onClick={() => void commitMutation.mutateAsync()} disabled={commitMutation.isPending}>
              {commitMutation.isPending ? <LoadingSpinner /> : '对，基本是这样'}
            </Button>
          </div>
        </Card>
      </Modal>
    </div>
  );
}
