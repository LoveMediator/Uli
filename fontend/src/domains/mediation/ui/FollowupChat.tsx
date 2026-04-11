import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Sparkles } from 'lucide-react';
import { mediationApi } from '@/domains/mediation/api/mediation-api';
import { getErrorMessage } from '@/shared/lib';
import { Button, Card, LoadingSpinner, Textarea } from '@/shared/ui';

type FollowupChatProps = {
  eventId: string;
};

type LocalMessage = {
  role: 'user' | 'assistant';
  content: string;
};

export function FollowupChat({ eventId }: FollowupChatProps) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<LocalMessage[]>([]);

  const followupMutation = useMutation({
    mutationFn: (value: string) => mediationApi.sendFollowupMessage(eventId, { message: value }),
    onSuccess: (data, userMessage) => {
      setMessages((current) => [
        ...current,
        { role: 'user', content: userMessage },
        {
          role: 'assistant',
          content: `${data.reply}\n\n本次上下文：最近消息 ${data.contextMeta.recentMessages} 条，快照 ${data.contextMeta.snapshots} 条，裁决结果 ${data.contextMeta.judgeResults} 条。`,
        },
      ]);
      setMessage('');
    },
  });

  return (
    <Card className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-accent-pink/15 p-3 text-accent-pink">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-base font-extrabold text-coffee-900">复盘追问</h3>
          <p className="text-xs text-coffee-800/60">继续追问建议、表达方式，或者后续相处策略。</p>
        </div>
      </div>

      <div className="max-h-64 space-y-3 overflow-y-auto rounded-3xl bg-milk-50 p-4">
        {messages.length === 0 ? (
          <p className="text-sm text-coffee-800/60">还没有追问记录，试着问问下一步该怎么做。</p>
        ) : (
          messages.map((item, index) => (
            <div
              key={`${item.role}-${index}`}
              className={
                item.role === 'assistant'
                  ? 'mr-8 rounded-3xl rounded-tl-md bg-white p-3 text-sm text-coffee-800'
                  : 'ml-8 rounded-3xl rounded-tr-md bg-coffee-100 p-3 text-sm text-coffee-900'
              }
            >
              {item.content}
            </div>
          ))
        )}
      </div>

      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          const value = message.trim();
          if (!value) {
            return;
          }
          void followupMutation.mutateAsync(value);
        }}
      >
        <Textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="比如：我现在更适合先道歉，还是先确认对方的感受？"
          rows={3}
        />
        {followupMutation.error ? <p className="text-xs font-semibold text-red-400">{getErrorMessage(followupMutation.error)}</p> : null}
        <Button fullWidth type="submit" disabled={followupMutation.isPending}>
          {followupMutation.isPending ? <LoadingSpinner /> : <Send className="mr-2 h-4 w-4" />}
          发送追问
        </Button>
      </form>
    </Card>
  );
}
