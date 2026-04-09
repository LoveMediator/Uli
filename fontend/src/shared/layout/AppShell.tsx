import type { PropsWithChildren } from 'react';
import { BottomNav } from './BottomNav';
import { DeviceFrame } from './DeviceFrame';

export function AppShell({ children }: PropsWithChildren) {
  return (
    <DeviceFrame>
      <main className="relative h-[812px] w-full overflow-hidden bg-milk-50">{children}</main>
      <BottomNav />
    </DeviceFrame>
  );
}
