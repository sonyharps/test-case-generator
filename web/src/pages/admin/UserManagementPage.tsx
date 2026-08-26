// src/pages/admin/UserManagementPage.tsx
import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/store/auth.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  listUsers,
  updateUser,
  deleteUser,
  type UserListItem,
} from "@/api/users";
import { listSquads, type SquadItem } from "@/api/squads";
import { hasMinRole, ROLE_LABELS } from "@/lib/roles";
import { cn } from "@/lib/utils";
import {
  Search,
  Trash2,
  Pencil,
  Users as UsersIcon,
  X,
  Mail,
  User as UserIcon,
  Shield,
  Building2,
  ToggleLeft,
} from "lucide-react";

const ROLES = ["qa_staff", "qa_lead", "kabag", "admin"] as const;

const ROLE_BADGE_STYLES: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  kabag: "bg-blue-100 text-blue-700",
  qa_lead: "bg-emerald-100 text-emerald-700",
  qa_staff: "bg-gray-200 text-gray-700",
};

interface EditForm {
  full_name: string;
  email: string;
  role: string;
  squad_id: string;
  is_active: boolean;
}

export default function UserManagementPage() {
  const token = useAuth((s) => s.accessToken);
  const currentUser = useAuth((s) => s.user);
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [squads, setSquads] = useState<SquadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<UserListItem | null>(null);

  // Edit modal state
  const [editing, setEditing] = useState<UserListItem | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    full_name: "",
    email: "",
    role: "qa_staff",
    squad_id: "",
    is_active: true,
  });
  const [editError, setEditError] = useState<string | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);

  const isAdmin = hasMinRole(currentUser?.role, "admin");

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [u, s] = await Promise.all([
        listUsers(token, { search: search || undefined, limit: 200 }),
        listSquads(token),
      ]);
      setUsers(u.users);
      setSquads(s.squads);
    } catch (err: any) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [token, search]);

  useEffect(() => {
    load();
  }, [load]);

  const openEdit = (user: UserListItem) => {
    setEditing(user);
    setEditError(null);
    setEditForm({
      full_name: user.full_name ?? "",
      email: user.email,
      role: user.role,
      squad_id: user.squad_id != null ? String(user.squad_id) : "",
      is_active: user.is_active,
    });
  };

  const handleSaveEdit = async () => {
    if (!token || !editing) return;
    setSavingEdit(true);
    setEditError(null);
    try {
      const payload: Record<string, any> = {
        full_name: editForm.full_name.trim() || null,
        email: editForm.email.trim(),
        role: editForm.role,
        squad_id: editForm.squad_id === "" ? null : Number(editForm.squad_id),
        is_active: editForm.is_active,
      };
      const updated = await updateUser(editing.id, payload, token);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setEditing(null);
    } catch (err: any) {
      setEditError(err.message || "Failed to save changes");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async () => {
    if (!token || !confirmDelete) return;
    setSavingId(confirmDelete.id);
    try {
      await deleteUser(confirmDelete.id, token);
      setUsers((prev) => prev.filter((u) => u.id !== confirmDelete.id));
      setConfirmDelete(null);
    } catch (err: any) {
      setError(err.message || "Failed to delete user");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <UsersIcon className="w-6 h-6 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="text-sm text-slate-500">
            Manage user profiles, roles, squad assignments, and account status.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start justify-between gap-2">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search username, email, name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Squad</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  Loading...
                </td>
              </tr>
            )}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No users found.
                </td>
              </tr>
            )}
            {users.map((u) => {
              const isSelf = u.id === currentUser?.id;
              const canEdit = !isSelf;
              return (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">
                      {u.username}
                      {isSelf && (
                        <span className="ml-2 text-xs text-slate-400">(you)</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">{u.email}</div>
                    {u.full_name && (
                      <div className="text-xs text-slate-400">{u.full_name}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide",
                        ROLE_BADGE_STYLES[u.role] ?? "bg-gray-100 text-gray-700"
                      )}
                    >
                      {ROLE_LABELS[u.role as keyof typeof ROLE_LABELS] ?? u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {u.squad_name ?? (
                      <span className="text-slate-400 italic">— None —</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-block px-2 py-0.5 rounded-full text-xs font-medium",
                        u.is_active
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-red-100 text-red-700"
                      )}
                    >
                      {u.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {canEdit && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEdit(u)}
                          className="h-8 w-8 p-0 text-slate-600 hover:text-blue-700 hover:bg-blue-50"
                          title="Edit user"
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                      )}
                      {isAdmin && !isSelf && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setConfirmDelete(u)}
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          title="Delete user"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Edit modal */}
      {editing && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 sticky top-0 bg-white">
              <div>
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Pencil className="w-4 h-4 text-blue-600" />
                  Edit User
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {editing.username} (id: {editing.id})
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => setEditing(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="px-6 py-5 space-y-4">
              {editError && (
                <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
                  {editError}
                </div>
              )}

              {/* Username (read-only) */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <UserIcon className="w-3 h-3" /> Username
                </label>
                <Input value={editing.username} disabled className="bg-slate-50 text-slate-500" />
                <p className="text-[11px] text-slate-400">Username cannot be changed.</p>
              </div>

              {/* Full name */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <UserIcon className="w-3 h-3" /> Full Name
                </label>
                <Input
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  placeholder="Full name (optional)"
                />
              </div>

              {/* Email */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <Mail className="w-3 h-3" /> Email
                </label>
                <Input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  placeholder="email@example.com"
                />
              </div>

              {/* Role */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <Shield className="w-3 h-3" /> Role
                </label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  disabled={!isAdmin && editForm.role === "admin"}
                  className={cn(
                    "w-full rounded-md border border-slate-200 px-3 py-2 text-sm",
                    "focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r} disabled={!isAdmin && r === "admin"}>
                      {ROLE_LABELS[r]}
                      {r === "admin" && !isAdmin && " (admin only)"}
                    </option>
                  ))}
                </select>
                {!isAdmin && (
                  <p className="text-[11px] text-slate-400">
                    Only admin can assign the Admin role.
                  </p>
                )}
              </div>

              {/* Squad */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <Building2 className="w-3 h-3" /> Squad
                </label>
                <select
                  value={editForm.squad_id}
                  onChange={(e) => setEditForm({ ...editForm, squad_id: e.target.value })}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">— None (unassigned) —</option>
                  {squads.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Active toggle */}
              <div className="flex items-center justify-between py-2 px-3 rounded-md bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-2">
                  <ToggleLeft className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="text-sm font-medium text-slate-900">
                      Account Status
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Disabled users cannot log in.
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setEditForm({ ...editForm, is_active: !editForm.is_active })}
                  className={cn(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    editForm.is_active ? "bg-emerald-500" : "bg-slate-300"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      editForm.is_active ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
              </div>
            </div>

            <div className="flex justify-end gap-2 px-6 py-4 border-t border-slate-100 sticky bottom-0 bg-white">
              <Button variant="outline" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button onClick={handleSaveEdit} disabled={savingEdit}>
                {savingEdit ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
            <div className="flex items-center gap-2 mb-3">
              <Trash2 className="w-5 h-5 text-red-600" />
              <h3 className="font-semibold text-slate-900">Delete user?</h3>
            </div>
            <p className="text-sm text-slate-600 mb-5">
              This will permanently delete{" "}
              <span className="font-medium">{confirmDelete.username}</span> and
              all their data. This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setConfirmDelete(null)}>
                Cancel
              </Button>
              <Button
                className="bg-red-600 hover:bg-red-700"
                onClick={handleDelete}
                disabled={savingId === confirmDelete.id}
              >
                {savingId === confirmDelete.id ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
