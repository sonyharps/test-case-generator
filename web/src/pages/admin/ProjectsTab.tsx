// src/pages/admin/ProjectsTab.tsx
// Tab "Proyek" di menu Tim: daftar proyek + mapping squad → proyek.
// Project ditentukan oleh squad: QA tidak memilih apa pun di wizard.
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/store/auth.store";
import {
  listProjects,
  createProject,
  deleteProject,
  setSquadProject,
  type ProjectItem,
} from "@/api/projects";
import { listSquads } from "@/api/squads";
import type { SquadItem } from "@/api/squads";

export default function ProjectsTab() {
  const token = useAuth((s) => s.accessToken);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [squads, setSquads] = useState<SquadItem[]>([]);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [p, s] = await Promise.all([listProjects(token), listSquads(token)]);
      setProjects(p);
      setSquads(s.squads || []);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal memuat data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!token || !newName.trim() || busy) return;
    setBusy(true);
    try {
      await createProject(
        { name: newName.trim(), code: newCode.trim() || undefined },
        token
      );
      setNewName("");
      setNewCode("");
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal membuat proyek");
    } finally {
      setBusy(false);
    }
  };

  const handleMap = async (squadId: number, projectId: number | null) => {
    if (!token || busy) return;
    setBusy(true);
    try {
      await setSquadProject(squadId, projectId, token);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal menyimpan mapping");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!token || busy) return;
    if (!confirm("Hapus proyek ini? Squad yang ter-map akan dilepas. Riwayat session tidak berubah.")) return;
    setBusy(true);
    try {
      await deleteProject(id, token);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal menghapus proyek");
    } finally {
      setBusy(false);
    }
  };

  const squadProjectId = (squadId: number): number | null => {
    const sq = squads.find((s) => s.id === squadId);
    return (sq as unknown as { project_id?: number | null })?.project_id ?? null;
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Daftar proyek */}
      <Card>
        <CardContent className="p-5">
          <h3 className="font-semibold text-slate-900 mb-0.5">Daftar Proyek</h3>
          <p className="text-xs text-slate-500 mb-4">
            Proyek diikuti otomatis oleh squad yang di-map ke proyek tersebut.
          </p>

          <div className="flex gap-2 mb-4 flex-wrap">
            <Input
              placeholder="Nama proyek (mis. Mobile Banking QRIS)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-72"
            />
            <Input
              placeholder="Kode (opsional)"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              className="w-40"
            />
            <Button onClick={handleCreate} disabled={busy || !newName.trim()}>
              Tambah Proyek
            </Button>
          </div>

          {loading ? (
            <p className="text-sm text-slate-400">Memuat…</p>
          ) : projects.length === 0 ? (
            <p className="text-sm text-slate-400 italic">
              Belum ada proyek. Tambahkan proyek pertama di atas, lalu map squad ke proyeknya.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b">
                    <th className="py-2 pr-4">Proyek</th>
                    <th className="py-2 pr-4">Kode</th>
                    <th className="py-2 pr-4">Squad</th>
                    <th className="py-2 pr-4">Session</th>
                    <th className="py-2 pr-4">Test Case</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {projects.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50">
                      <td className="py-2.5 pr-4 font-medium text-slate-900">{p.name}</td>
                      <td className="py-2.5 pr-4 text-slate-500">{p.code || "—"}</td>
                      <td className="py-2.5 pr-4 text-slate-600">
                        {p.squads.length > 0
                          ? p.squads.map((s) => s.name).join(", ")
                          : <span className="text-slate-400">belum di-map</span>}
                      </td>
                      <td className="py-2.5 pr-4 text-slate-600">{p.session_count}</td>
                      <td className="py-2.5 pr-4 text-slate-600">{p.test_case_count}</td>
                      <td className="py-2.5 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(p.id)}
                          disabled={busy}
                          className="text-red-600 hover:text-red-700"
                        >
                          Hapus
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Mapping squad → proyek */}
      <Card>
        <CardContent className="p-5">
          <h3 className="font-semibold text-slate-900 mb-0.5">Mapping Squad → Proyek</h3>
          <p className="text-xs text-slate-500 mb-4">
            Anggota squad yang di-map akan otomatis tercatat di proyek tersebut
            saat generate &amp; upload dokumen — QA tidak perlu memilih apa pun.
          </p>
          {squads.length === 0 ? (
            <p className="text-sm text-slate-400 italic">Belum ada squad.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b">
                    <th className="py-2 pr-4">Squad</th>
                    <th className="py-2 pr-4">Anggota</th>
                    <th className="py-2">Proyek aktif</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {squads.map((sq) => {
                    const pid = squadProjectId(sq.id);
                    return (
                      <tr key={sq.id} className="hover:bg-slate-50">
                        <td className="py-2.5 pr-4 font-medium text-slate-900">{sq.name}</td>
                        <td className="py-2.5 pr-4 text-slate-500">{sq.member_count}</td>
                        <td className="py-2.5">
                          <select
                            value={pid ?? ""}
                            onChange={(e) =>
                              handleMap(sq.id, e.target.value ? Number(e.target.value) : null)
                            }
                            disabled={busy}
                            className="border border-slate-300 rounded-md px-2.5 py-1.5 text-sm min-w-56 bg-white"
                          >
                            <option value="">— (belum di-set) —</option>
                            {projects.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
