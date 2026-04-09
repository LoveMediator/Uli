import type { InputHTMLAttributes } from 'react';
import { cn } from '@/shared/lib';

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

export function Input({ className, label, error, ...props }: InputProps) {
  return (
    <label className="block space-y-2">
      {label ? <span className="text-sm font-bold text-coffee-900">{label}</span> : null}
      <input
        className={cn(
          'w-full rounded-2xl border border-milk-200 bg-white px-4 py-3 text-sm text-coffee-900 outline-none transition placeholder:text-coffee-800/40 focus:border-milk-400 focus:ring-2 focus:ring-milk-200',
          error && 'border-red-300 focus:border-red-300 focus:ring-red-100',
          className,
        )}
        {...props}
      />
      {error ? <span className="text-xs font-semibold text-red-400">{error}</span> : null}
    </label>
  );
}
