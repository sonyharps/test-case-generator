// src/components/auth/UserProfile.tsx
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth.store";
import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";

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

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
        <User className="w-4 h-4 text-gray-600" />
        <div className="text-sm">
          <p className="font-medium text-gray-900">{user.username}</p>
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
