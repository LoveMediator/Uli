import type { PropsWithChildren } from 'react';
import { cn } from '@/lib/cn';

type BottomSheetProps = PropsWithChildren<{
  expanded: boolean;
  onToggle: () => void;
}>;

export function BottomSheet({ children, expanded, onToggle }: BottomSheetProps) {
  return (
    <div
      className={cn(
        'absolute bottom-0 left-0 right-0 z-20 flex flex-col rounded-t-[40px] border border-gray-100 bg-white pb-20 shadow-[0_-10px_40px_rgba(0,0,0,0.08)] transition-all duration-500',
        expanded ? 'h-[82%]' : 'h-[46%]',
      )}
    >
      <button className="flex h-10 w-full items-center justify-center" onClick={onToggle}>
        <span className="h-1 w-10 rounded-full bg-gray-300" />
      </button>
      {children}
    </div>
  );
}
