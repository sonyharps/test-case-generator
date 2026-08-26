// src/pages/admin/SquadManagementPage.tsx
import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/store/auth.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  listSquads,
  createSquad,
  updateSquad,
  deleteSquad,
  getSquadMembers,
  type SquadItem,
  type SquadDetail,
} from "@/api/squads";
import { Users, Plus, Pencil, Trash2, ChevronRight, X } from "lucide-react";

export default function SquadManagementPage() {
  const token = useAuth((s) => s.accessToken);
  const [squads, setSquads] = useState<SquadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  // Edit modal
  const [editing, setEditing] = useState<SquadItem | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  // Members panel
  const [membersDetail, setMembersDetail] = useState<SquadDetail | null>(null);
  const [loadingMembers, setLoadingMembers] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listSquads(token);
      setSquads(res.squads);
    } catch (err: any) {
      setError(err.message || "Failed to load squads");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!token || !newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createSquad(
        { name: newName.trim(), description: newDesc.trim() || undefined },
        token
      );
      setSquads((prev) => [...prev, { ...created, member_count: 0 }]);
      setNewName("");
      setNewDesc("");
    } catch (err: any) {
      setError(err.message || "Failed to create squad");
    } finally {
      setCreating(false);
    }
  };

  const openEdit = (s: SquadItem) => {
    setEditing(s);
    setEditName(s.name);
    setEditDesc(s.description ?? "");
  };

  const handleSaveEdit = async () => {
    if (!token || !editing) return;
    setSavingEdit(true);
    try {
      const updated = await updateSquad(
        editing.id,
        { name: editName.trim(), description: editDesc.trim() || undefined },
        token
      );
      setSquads((prev) =>
        prev.map((s) => (s.id === updated.id ? { ...s, ...updated } : s))
      );
      setEditing(null);
    } catch (err: any) {
      setError(err.message || "Failed to update squad");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async (s: SquadItem) => {
    if (!token) return;
    if (!confirm(`Delete squad "${s.name}"? Members will be unassigned.`)) return;
    try {
      await deleteSquad(s.id, token);
      setSquads((prev) => prev.filter((x) => x.id !== s.id));
    } catch (err: any) {
      setError(err.message || "Failed to delete squad");
    }
  };

  const openMembers = async (s: SquadItem) => {
    if (!token) return;
    setLoadingMembers(true);
    setMembersDetail(null);
    try {
      const detail = await getSquadMembers(s.id, token);
      setMembersDetail(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load members");
    } finally {
      setLoadingMembers(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Users className="w-6 h-6 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Squads</h1>
          <p className="text-sm text-slate-500">
            Manage QA teams. Squad leads can see their members' data.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Create squad */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium text-slate-900 flex items-center gap-2">
          <Plus className="w-4 h-4" /> Create new squad
        </h2>
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            placeholder="Squad name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="sm:max-w-xs"
          />
          <Input
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="sm:flex-1"
          />
          <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
            {creating ? "Creating..." : "Create"}
          </Button>
        </div>
      </div>

      {/* Squad list */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {loading && (
          <div className="col-span-full text-center py-8 text-slate-400">
            Loading squads...
          </div>
        )}
        {!loading && squads.length === 0 && (
          <div className="col-span-full text-center py-8 text-slate-400">
            No squads yet. Create one above.
          </div>
        )}
        {squads.map((s) => (
          <div
            key={s.id}
            className="rounded-lg border border-slate-200 bg-white p-4 space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">{s.name}</h3>
                {s.description && (
                  <p className="text-xs text-slate-500 mt-0.5">{s.description}</p>
                )}
              </div>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => openEdit(s)}
                  className="h-8 w-8 p-0"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleDelete(s)}
                  className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-xs text-slate-500">
                {s.member_count} member{s.member_count !== 1 ? "s" : ""}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => openMembers(s)}
                className="h-7 text-xs"
              >
                View members
                <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit modal */}
      {editing && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">Edit squad</h3>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => setEditing(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-600">Name</label>
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
              <label className="text-xs font-medium text-slate-600">
                Description
              </label>
              <Input
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button onClick={handleSaveEdit} disabled={savingEdit}>
                {savingEdit ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Members panel */}
      {membersDetail && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">
                  {membersDetail.name} members
                </h3>
                <p className="text-xs text-slate-500">
                  {membersDetail.members.length} member
                  {membersDetail.members.length !== 1 ? "s" : ""}
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0"
                onClick={() => setMembersDetail(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {loadingMembers && (
                <p className="text-sm text-slate-400 text-center py-4">
                  Loading...
                </p>
              )}
              {!loadingMembers && membersDetail.members.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-4">
                  No members assigned. Assign users from the User Management page.
                </p>
              )}
              {membersDetail.members.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between px-3 py-2 rounded-md bg-slate-50"
                >
                  <div>
                    <div className="text-sm font-medium text-slate-900">
                      {m.username}
                    </div>
                    <div className="text-xs text-slate-500">{m.email}</div>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                    {m.role}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
