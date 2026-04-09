import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';
import { cn } from '@/shared/lib';

export type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    fullWidth?: boolean;
  }
>;

export function Button({
  children,
  className,
  variant = 'primary',
  fullWidth = false,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center rounded-2xl px-4 py-3 text-sm font-bold transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60',
        variant === 'primary' && 'bg-coffee-800 text-white shadow-lg shadow-coffee-900/20 hover:bg-coffee-900',
        variant === 'secondary' && 'border border-milk-200 bg-white text-coffee-900 hover:bg-milk-50',
        variant === 'ghost' && 'bg-transparent text-coffee-800 hover:bg-white/60',
        variant === 'danger' && 'bg-red-400 text-white shadow-lg shadow-red-200 hover:bg-red-500',
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
