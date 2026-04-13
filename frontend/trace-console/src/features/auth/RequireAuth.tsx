import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ROUTE_PERMISSION_MAP } from "./permissions";
import { useAuth } from "./useAuth";
import { usePermission } from "./usePermission";

interface RequireAuthProps {
  children: ReactNode;
}

export function RequireAuth({ children }: RequireAuthProps) {
  const { status } = useAuth();
  const { hasPermission } = usePermission();
  const location = useLocation();

  if (status === "idle" || status === "loading") {
    return <div style={{ padding: 24 }}>Loading...</div>;
  }

  if (status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const matchedRoutePermission = ROUTE_PERMISSION_MAP.find((item) => location.pathname.startsWith(item.pathPrefix));
  if (matchedRoutePermission && !hasPermission(matchedRoutePermission.permission)) {
    return <div style={{ padding: 24 }}>当前账号没有访问该页面的权限。</div>;
  }

  return <>{children}</>;
}
