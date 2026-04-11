import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle2, Send } from 'lucide-react';
import { mediationApi } from '@/domains/mediation/api/mediation-api';
import type { AnalysisSessionCommitData, AnalysisSessionMessagePayload } from '@/shared/api/types';
import { getErrorMessage } from '@/shared/lib';
import { Button, Card, LoadingSpinner } from '@/shared/ui';

export interface AnalysisChatPanelProps {
  sessionId: string;
  initialMessages: AnalysisSessionMessagePayload[];
  initialCanCommit: boolean;
  initialFactSummary: string | null;
  onCommitted: (data: AnalysisSessionCommitData) => void;
  commitLabel?: string;
  inputPlaceholder?: string;
}

export function AnalysisChatPanel({
  sessionId,
  initialMessages,
  initialCanCommit,
  initialFactSummary,
  onCommitted,
  commitLabel = '确认提交',
  inputPlaceholder = '和 AI 说说发生了什么...',
}: AnalysisChatPanelProps) {
  const [messages, setMessages] = useState<AnalysisSessionMessagePayload[]>(initialMessages);
  const [inputText, setInputText] = useState('');
  const [canCommit, setCanCommit] = useState(initialCanCommit);
  const [factSummary, setFactSummary] = useState<string | null>(initialFactSummary);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => mediationApi.sendAnalysisMessage(sessionId, { message }),
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

  const commitMutation = useMutation({
    mutationFn: () => mediationApi.commitAnalysisSession(sessionId),
    onSuccess: (data) => {
      onCommitted(data);
    },
  });

  const handleSend = () => {
    const text = inputText.trim();
    if (!text || sendMessageMutation.isPending) {
      return;
    }

    void sendMessageMutation.mutateAsync(text);
  };

  return (
    <>
      {messages.map((msg, index) => (
        <div key={`${msg.role}-${index}`} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
          {msg.role === 'assistant' ? (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 text-xs font-bold text-coffee-900 shadow-sm">
              AI
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
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-white bg-milk-300 text-xs font-bold text-coffee-900 shadow-sm">
            AI
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
            <span className="text-sm font-bold">AI 认为事实已经足够清晰，可以提交了</span>
          </div>
          <div className="rounded-2xl bg-white px-4 py-3 text-sm leading-7 text-coffee-800">
            <p className="mb-1 text-xs font-bold text-coffee-800/40">事实摘要</p>
            {factSummary}
          </div>
          {commitMutation.error ? (
            <p className="text-sm font-semibold text-red-400">{getErrorMessage(commitMutation.error)}</p>
          ) : null}
          <Button fullWidth disabled={commitMutation.isPending} onClick={() => void commitMutation.mutateAsync()}>
            {commitMutation.isPending ? <LoadingSpinner /> : commitLabel}
          </Button>
        </Card>
      ) : null}

      {sendMessageMutation.error ? (
        <p className="text-sm font-semibold text-red-400">{getErrorMessage(sendMessageMutation.error)}</p>
      ) : null}

      <div ref={chatEndRef} />

      <div className="flex items-center gap-2 rounded-[24px] border border-milk-100 bg-white p-2 shadow-lg">
        <input
          className="flex-1 bg-transparent px-3 py-2 text-sm text-coffee-800 outline-none placeholder:text-coffee-800/40"
          placeholder={inputPlaceholder}
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          disabled={sendMessageMutation.isPending}
        />
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-coffee-800 text-white transition-colors hover:bg-coffee-900 disabled:opacity-40"
          disabled={!inputText.trim() || sendMessageMutation.isPending}
          onClick={handleSend}
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </>
  );
}
