import type { PropsWithChildren } from 'react';
import { cn } from '@/shared/lib';

export type DeviceFrameProps = PropsWithChildren<{
  className?: string;
}>;

export function DeviceFrame({ children, className }: DeviceFrameProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-milk-100 via-milk-50 to-coffee-50 px-4 py-6">
      <div
        className={cn(
          'mx-auto flex min-h-[812px] w-full max-w-[420px] overflow-hidden rounded-[40px] border-[6px] border-gray-800 bg-milk-50 shadow-2xl ring-8 ring-gray-900/90',
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
