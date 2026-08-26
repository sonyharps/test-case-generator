// src/lib/roles.ts
// Mirror of app/models/squad.py ROLE_LEVELS. Keep in sync.

export type Role = "admin" | "kabag" | "qa_lead" | "qa_staff";

export const ROLE_LEVELS: Record<string, number> = {
  qa_staff: 10,
  qa_lead: 20,
  kabag: 40,
  admin: 80,
};

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Admin",
  kabag: "Kabag",
  qa_lead: "QA Lead",
  qa_staff: "QA Staff",
};

/** Returns true if `userRole` has at least the privilege of `minRole`. */
export function hasMinRole(
  userRole: string | undefined | null,
  minRole: string
): boolean {
  if (!userRole) return false;
  const userLevel = ROLE_LEVELS[userRole] ?? 0;
  const requiredLevel = ROLE_LEVELS[minRole] ?? 0;
  return userLevel >= requiredLevel;
}
