import { useAuth } from "./useAuth";

const SUPER_PERMISSION = "*";

export function usePermission() {
  const { profile } = useAuth();
  const permissions = profile?.permissions ?? [];
  const hasSuperPermission = permissions.includes(SUPER_PERMISSION);

  function hasPermission(code: string) {
    return hasSuperPermission || permissions.includes(code);
  }

  function hasAnyPermission(codes: string[]) {
    return codes.length === 0 || hasSuperPermission || codes.some((code) => permissions.includes(code));
  }

  function hasAllPermissions(codes: string[]) {
    return codes.length === 0 || hasSuperPermission || codes.every((code) => permissions.includes(code));
  }

  return {
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions
  };
}
