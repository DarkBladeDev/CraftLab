import { UserContext } from "../../../api";

export function checkRoleAccess(
  user: UserContext,
  requiredRoles?: string[],
  allowBreakGlass: boolean = true
): { authorized: boolean; reason?: string } {
  if (!requiredRoles || requiredRoles.length === 0) {
    return { authorized: true };
  }

  if (allowBreakGlass && user.is_break_glass) {
    return { authorized: true };
  }

  const hasRole = requiredRoles.some((role) => user.roles.includes(role));
  if (hasRole) {
    return { authorized: true };
  }

  return {
    authorized: false,
    reason: `Acción restringida. Requiere rol: ${requiredRoles.join(", ")}`,
  };
}
