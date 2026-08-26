// src/components/auth/UserProfile.tsx
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth.store";
import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";
import { ROLE_LABELS } from "@/lib/roles";
import { cn } from "@/lib/utils";

const ROLE_BADGE_STYLES: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  kabag: "bg-blue-100 text-blue-700",
  qa_lead: "bg-emerald-100 text-emerald-700",
  qa_staff: "bg-gray-200 text-gray-700",
};

export default function UserProfile() {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate("/login")}>
          Sign In
        </Button>
        <Button size="sm" onClick={() => navigate("/register")}>
          Sign Up
        </Button>
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const roleLabel = ROLE_LABELS[user.role as keyof typeof ROLE_LABELS] ?? user.role;
  const badgeClass = ROLE_BADGE_STYLES[user.role] ?? "bg-gray-200 text-gray-700";

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
        <User className="w-4 h-4 text-gray-600" />
        <div className="text-sm">
          <div className="flex items-center gap-2">
            <p className="font-medium text-gray-900">{user.username}</p>
            <span
              className={cn(
                "px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide",
                badgeClass
              )}
            >
              {roleLabel}
            </span>
          </div>
          {user.full_name && (
            <p className="text-xs text-gray-600">{user.full_name}</p>
          )}
        </div>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={handleLogout}
        className="flex items-center gap-2"
      >
        <LogOut className="w-4 h-4" />
        Logout
      </Button>
    </div>
  );
}
