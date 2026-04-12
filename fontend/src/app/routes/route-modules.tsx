import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

type RouteComponent = ComponentType<Record<string, never>>;

type PreloadableComponent = LazyExoticComponent<RouteComponent> & {
  preload: () => Promise<{ default: RouteComponent }>;
};

function lazyWithPreload(factory: () => Promise<{ default: RouteComponent }>): PreloadableComponent {
  const Component = lazy(factory) as PreloadableComponent;
  Component.preload = factory;
  return Component;
}

export const LoginPage = lazyWithPreload(() =>
  import('@/domains/auth/page/LoginPage').then((module) => ({ default: module.LoginPage })),
);

export const RegisterPage = lazyWithPreload(() =>
  import('@/domains/auth/page/RegisterPage').then((module) => ({ default: module.RegisterPage })),
);

export const HomePage = lazyWithPreload(() =>
  import('@/domains/home/page/HomePage').then((module) => ({ default: module.HomePage })),
);

export const MediationPage = lazyWithPreload(() =>
  import('@/domains/mediation/page/MediationPage').then((module) => ({ default: module.MediationPage })),
);

export const CalendarPage = lazyWithPreload(() =>
  import('@/domains/calendar/page/CalendarPage').then((module) => ({ default: module.CalendarPage })),
);

export const ProfilePage = lazyWithPreload(() =>
  import('@/domains/profile/page/ProfilePage').then((module) => ({ default: module.ProfilePage })),
);

export const InvitePage = lazyWithPreload(() =>
  import('@/domains/invite/page/InvitePage').then((module) => ({ default: module.InvitePage })),
);

export const RelationshipPage = lazyWithPreload(() =>
  import('@/domains/relationship/page/RelationshipPage').then((module) => ({ default: module.RelationshipPage })),
);
