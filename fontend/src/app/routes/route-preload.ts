import {
  CalendarPage,
  HomePage,
  InvitePage,
  LoginPage,
  MediationPage,
  ProfilePage,
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
];

const allPreloaders = [
  LoginPage.preload,
  RegisterPage.preload,
  InvitePage.preload,
  HomePage.preload,
  MediationPage.preload,
  CalendarPage.preload,
  ProfilePage.preload,
];

export async function preloadCriticalRoute(pathname: string) {
  const matched = routePreloaders.find((route) => route.test(pathname));
  if (!matched) {
    await HomePage.preload();
    return;
  }

  await matched.preload();
}

export async function preloadSecondaryRoutes() {
  await Promise.allSettled(allPreloaders.map((preload) => preload()));
}
