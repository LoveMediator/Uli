import { useEffect } from 'react';
import { removeMessage, useMessageStore } from '@/shared/ui/message-store';

const toneClassName = {
  info: 'border-milk-200 bg-white text-coffee-900',
  success: 'border-accent-green/40 bg-accent-green/10 text-coffee-900',
  warning: 'border-yellow-300 bg-yellow-50 text-coffee-900',
  error: 'border-red-200 bg-red-50 text-coffee-900',
} as const;

export function MessageViewport() {
  const items = useMessageStore((state) => state.items);

  useEffect(() => {
    if (items.length === 0) {
      return undefined;
    }

    const timers = items.map((item) =>
      window.setTimeout(() => {
        removeMessage(item.id);
      }, 3200),
    );

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [items]);

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-[100] flex justify-center px-4">
      <div className="w-full max-w-md space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto rounded-2xl border px-4 py-3 text-sm font-semibold shadow-lg ${toneClassName[item.tone]}`}
          >
            {item.text}
          </div>
        ))}
      </div>
    </div>
  );
}
