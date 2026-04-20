import {
  CalendarPage,
  HomePage,
  InvitePage,
  LoginPage,
  MediationPage,
  ProfilePage,
  RelationshipPage,
  RegisterPage,
} from '@/app/routes/route-modules';

const routePreloaders = [
  { test: (pathname: string) => pathname === '/login', preload: LoginPage.preload },
  { test: (pathname: string) => pathname === '/register', preload: RegisterPage.preload },
  { test: (pathname: string) => pathname.startsWith('/invite/'), preload: InvitePage.preload },
  { test: (pathname: string) => pathname === '/app/home' || pathname === '/app', preload: HomePage.preload },
  { test: (pathname: string) => pathname === '/app/mediation', preload: MediationPage.preload },
  { test: (pathname: string) => pathname === '/app/calendar', preload: CalendarPage.preload },
  { test: (pathname: string) => pathname === '/app/profile', preload: ProfilePage.preload },
  { test: (pathname: string) => pathname === '/app/relationship', preload: RelationshipPage.preload },
];

const allPreloaders = [
  LoginPage.preload,
  RegisterPage.preload,
  InvitePage.preload,
  HomePage.preload,
  MediationPage.preload,
  CalendarPage.preload,
  ProfilePage.preload,
  RelationshipPage.preload,
];

function getSecondaryPreloaders(pathname: string) {
  const matched = routePreloaders.find((route) => route.test(pathname));

  if (!matched) {
    return allPreloaders;
  }

  return allPreloaders.filter((preload) => preload !== matched.preload);
}

export async function preloadCriticalRoute(pathname: string) {
  const matched = routePreloaders.find((route) => route.test(pathname));
  if (!matched) {
    await HomePage.preload();
    return;
  }

  await matched.preload();
}

export function preloadSecondaryRoutes(pathname: string) {
  const preloaders = getSecondaryPreloaders(pathname);

  if (preloaders.length === 0) {
    return;
  }

  const runPreloads = () => {
    void Promise.allSettled(preloaders.map((preload) => preload()));
  };

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(runPreloads, { timeout: 1500 });
    return;
  }

  globalThis.setTimeout(runPreloads, 0);
}
