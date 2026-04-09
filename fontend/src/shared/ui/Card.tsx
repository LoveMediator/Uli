import type { PropsWithChildren } from 'react';
import { cn } from '@/shared/lib';

export type CardProps = PropsWithChildren<{
  className?: string;
}>;

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn('rounded-[28px] border border-white/80 bg-white/90 p-5 shadow-soft', className)}>
      {children}
    </div>
  );
}
