import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { calendarApi } from '@/domains/calendar/api/calendar-api';
import { getErrorMessage } from '@/shared/lib';
import { Button, Card, Modal, Textarea } from '@/shared/ui';

type ReviewEditorDrawerProps = {
  reviewId: string | null;
  open: boolean;
  onClose: () => void;
  onUpdated: () => void;
};

export function ReviewEditorDrawer({ reviewId, open, onClose, onUpdated }: ReviewEditorDrawerProps) {
  const [draftContent, setDraftContent] = useState<string | null>(null);

  const reviewQuery = useQuery({
    queryKey: ['review-detail', reviewId],
    queryFn: () => calendarApi.getReview(reviewId!),
    enabled: open && !!reviewId,
  });

  const content = draftContent ?? reviewQuery.data?.content ?? '';

  const updateMutation = useMutation({
    mutationFn: () => calendarApi.updateReview(reviewId!, { content }),
    onSuccess: () => {
      onUpdated();
      onClose();
    },
  });

  return (
    <Modal open={open} onClose={onClose}>
      <Card className="space-y-4 rounded-[32px]">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Review</p>
          <h3 className="mt-1 text-xl font-extrabold text-coffee-900">查看与编辑复盘</h3>
        </div>

        {reviewQuery.isLoading ? <p className="text-sm text-coffee-800/60">正在加载复盘详情...</p> : null}

        {reviewQuery.data ? (
          <>
            <div className="rounded-3xl bg-milk-50 px-4 py-3 text-xs text-coffee-800/60">
              来源：{reviewQuery.data.source} · 更新时间：{new Date(reviewQuery.data.updatedAt).toLocaleString('zh-CN')}
            </div>
            <Textarea value={content} onChange={(event) => setDraftContent(event.target.value)} rows={9} />
          </>
        ) : null}

        {reviewQuery.error ? (
          <p className="text-sm font-semibold text-red-400">{getErrorMessage(reviewQuery.error)}</p>
        ) : null}

        {updateMutation.error ? (
          <p className="text-sm font-semibold text-red-400">{getErrorMessage(updateMutation.error)}</p>
        ) : null}

        <div className="flex gap-3">
          <Button fullWidth variant="secondary" onClick={onClose}>
            取消
          </Button>
          <Button
            fullWidth
            onClick={() => void updateMutation.mutateAsync()}
            disabled={!content.trim() || updateMutation.isPending}
          >
            保存
          </Button>
        </div>
      </Card>
    </Modal>
  );
}
