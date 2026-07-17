"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";

type RecordItem = {
  id: string;
  draft_id: string | null;
  filename: string;
  status: string;
  pdf_status: string;
  pdf_expires_at?: string | null;
  created_at: string;
};

function pdfLabel(status: string) {
  if (status === "archived") return "Archived";
  if (status === "expired" || status === "deleted") return "PDF Expired";
  return "Available";
}

export default function HistoryPage() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [search, setSearch] = useState("");

  async function load() {
    const result = await api<{ records: RecordItem[] }>(`/history${search ? `?search=${encodeURIComponent(search)}` : ""}`);
    setRecords(result.records);
  }

  useEffect(() => {
    load().catch(() => setRecords([]));
  }, []);

  return (
    <AppShell>
      <section className="grid gap-5">
        <div>
          <h1 className="text-3xl font-bold text-rl-textStrong">History</h1>
          <p className="mt-2">Reopen previous records and regenerate edited versions.</p>
        </div>
        <div className="flex gap-3">
          <input className="rl-input max-w-md" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search vehicle no, customer, insurer, date, status" />
          <button className="rl-button rl-button-secondary" type="button" onClick={load}>
            <Search aria-hidden="true" size={18} />
            Search
          </button>
        </div>
        <div className="rl-panel overflow-x-auto">
          <table className="rl-table min-w-[720px]">
            <thead>
              <tr>
                <th>Status</th>
                <th>File</th>
                <th>PDF</th>
                <th>Uploaded</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id}>
                  <td><StatusBadge status={record.status} /></td>
                  <td className="font-bold text-rl-textStrong">{record.filename}</td>
                  <td>{pdfLabel(record.pdf_status)}</td>
                  <td>{new Date(record.created_at).toLocaleString()}</td>
                  <td>{record.draft_id ? <Link className="rl-button rl-button-secondary" href={`/review/${record.draft_id}`}>Open</Link> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
