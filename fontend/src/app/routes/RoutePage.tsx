import { Suspense, type ComponentType, type LazyExoticComponent } from 'react';

type RouteComponent = ComponentType<Record<string, never>>;

type RoutePageProps = {
  component: LazyExoticComponent<RouteComponent>;
};

export function RoutePage({ component: Component }: RoutePageProps) {
  return (
    <Suspense fallback={<div className="h-full" />}>
      <Component />
    </Suspense>
  );
}
