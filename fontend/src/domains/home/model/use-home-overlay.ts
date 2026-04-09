import { useAppStore } from '@/app/model/app-store';

export function useHomeOverlay() {
  const homeOverlayOpen = useAppStore((state) => state.homeOverlayOpen);
  const setHomeOverlayOpen = useAppStore((state) => state.setHomeOverlayOpen);

  return {
    homeOverlayOpen,
    setHomeOverlayOpen,
  };
}
