import { cn } from "@/lib/utils";
import { type ComponentType } from "react";

interface SidebarItemProps {
  icon: ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export function SidebarItem({ icon: Icon, label, active, onClick }: SidebarItemProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 px-4 py-2 rounded-lg cursor-pointer text-sm transition-colors",
        active ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-gray-800 hover:text-white"
      )}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </div>
  );
}
