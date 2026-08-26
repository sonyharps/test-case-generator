// src/components/auth/ProtectedRoute.tsx
import { Navigate } from "react-router-dom";
import { useAuth } from "@/store/auth.store";
import { hasMinRole } from "@/lib/roles";

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** If set, requires the user's role to be >= the minimum listed here. */
  allowedRoles?: string[];
}

export default function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
  const isAuthenticated = useAuth((state) => state.isAuthenticated);
  const user = useAuth((state) => state.user);

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Role check: allowedRoles is a list of minimum roles; user passes if
  // they meet ANY of them (treated as "at least this role").
  if (allowedRoles && allowedRoles.length > 0) {
    const ok = allowedRoles.some((r) => hasMinRole(user?.role, r));
    if (!ok) {
      return <Navigate to="/forbidden" replace />;
    }
  }

  return <>{children}</>;
}
