import { AnimatePresence, motion } from 'framer-motion';
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth';
import { RoutePage } from '@/app/routes/RoutePage';
import {
  CalendarPage,
  HomePage,
  InvitePage,
  LoginPage,
  MediationPage,
  ProfilePage,
  RegisterPage,
  RelationshipPage,
} from '@/app/routes/route-modules';
import { AppShell } from '@/shared/layout';

function AnimatedOutlet() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2 }}
        className="h-full"
      >
        <Outlet />
      </motion.div>
    </AnimatePresence>
  );
}

function RequireAuth() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function PublicOnly() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/app/home" replace />;
  }

  return <Outlet />;
}

function ShellRoutes() {
  return (
    <AppShell>
      <AnimatedOutlet />
    </AppShell>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnly />}>
          <Route path="/login" element={<RoutePage component={LoginPage} />} />
          <Route path="/register" element={<RoutePage component={RegisterPage} />} />
        </Route>

        <Route path="/invite/:eventId" element={<RoutePage component={InvitePage} />} />

        <Route element={<RequireAuth />}>
          <Route path="/app" element={<ShellRoutes />}>
            <Route index element={<Navigate to="/app/home" replace />} />
            <Route path="home" element={<RoutePage component={HomePage} />} />
            <Route path="mediation" element={<RoutePage component={MediationPage} />} />
            <Route path="calendar" element={<RoutePage component={CalendarPage} />} />
            <Route path="profile" element={<RoutePage component={ProfilePage} />} />
            <Route path="relationship" element={<RoutePage component={RelationshipPage} />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/app/home" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
