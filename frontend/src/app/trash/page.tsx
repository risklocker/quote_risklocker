"use client";

import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";

type TrashRecord = { id: string; filename: string; status: string; created_at: string };

export default function TrashPage() {
  const [records, setRecords] = useState<TrashRecord[]>([]);

  async function load() {
    const result = await api<{ records: TrashRecord[] }>("/trash");
    setRecords(result.records);
  }

  async function restore(id: string) {
    await api(`/trash/${id}/restore`, { method: "POST", body: JSON.stringify({}) });
    await load();
  }

  useEffect(() => {
    load().catch(() => setRecords([]));
  }, []);

  return (
    <AppShell>
      <section className="grid gap-5">
        <div>
          <h1 className="text-3xl font-bold text-rl-textStrong">Trash</h1>
          <p className="mt-2">Deleted records stay here for 14 days before permanent deletion.</p>
        </div>
        <div className="rl-panel overflow-x-auto">
          <table className="rl-table min-w-[720px]">
            <thead>
              <tr>
                <th>Status</th>
                <th>File</th>
                <th>Deleted</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id}>
                  <td><StatusBadge status="Deleted" /></td>
                  <td className="font-bold text-rl-textStrong">{record.filename}</td>
                  <td>{new Date(record.created_at).toLocaleString()}</td>
                  <td>
                    <button className="rl-button rl-button-secondary" type="button" onClick={() => restore(record.id)}>
                      <RotateCcw aria-hidden="true" size={18} />
                      Restore
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
