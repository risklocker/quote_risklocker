"use client";

import { useEffect, useState } from "react";
import { Plus, RefreshCw, RotateCcw, Save } from "lucide-react";
import { AdminNav } from "@/components/admin-nav";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";

type User = { id: string; email: string; role: string; status: string };
type Check = { name: string; status: string; message: string };

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Staff");
  const [companyName, setCompanyName] = useState("");
  const [templateName, setTemplateName] = useState("");
  const [benefit, setBenefit] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [userResult, checkResult] = await Promise.all([
        api<{ users: User[] }>("/users"),
        api<{ checks: Check[] }>("/system/checks")
      ]);
      setUsers(userResult.users);
      setChecks(checkResult.checks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin data.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createUser(event: React.FormEvent) {
    event.preventDefault();
    await api("/users", { method: "POST", body: JSON.stringify({ email, role }) });
    setEmail("");
    await load();
  }

  async function revokeSessions(userId: string) {
    try {
      await api(`/users/${userId}/sessions/revoke`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not revoke sessions.");
    }
  }

  async function saveCompany(event: React.FormEvent) {
    event.preventDefault();
    await api("/admin/companies", { method: "POST", body: JSON.stringify({ name: companyName, category: "Motor", detection_phrases: [companyName] }) });
    setCompanyName("");
  }

  async function saveTemplate(event: React.FormEvent) {
    event.preventDefault();
    await api("/admin/templates", { method: "POST", body: JSON.stringify({ name: templateName, insurance_type: "Motor" }) });
    setTemplateName("");
  }

  async function saveBenefit(event: React.FormEvent) {
    event.preventDefault();
    await api("/admin/benefits", { method: "POST", body: JSON.stringify({ label: benefit, section: "Motor Benefits" }) });
    setBenefit("");
  }

  return (
    <AppShell>
      <section className="grid gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-rl-textStrong">Admin</h1>
            <p className="mt-2">Manage users, insurance companies, templates, benefits, and system checks.</p>
          </div>
          <button className="rl-button rl-button-secondary" type="button" onClick={load}>
            <RefreshCw aria-hidden="true" size={18} />
            Refresh
          </button>
        </div>
        <AdminNav />
        {error ? <p className="rounded-md border border-rl-red bg-red-50 p-3 font-bold text-rl-red">{error}</p> : null}
        <div className="grid gap-5 xl:grid-cols-2">
          <form className="rl-panel grid gap-3 p-5" onSubmit={createUser}>
            <h2 className="text-xl font-bold text-rl-textStrong">Users & Roles</h2>
            <input className="rl-input" type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            <select className="rl-input" value={role} onChange={(event) => setRole(event.target.value)}>
              <option>Staff</option>
              <option>Manager</option>
              <option>Admin</option>
            </select>
            <button className="rl-button w-fit" type="submit"><Plus aria-hidden="true" size={18} />Add user</button>
            <div className="overflow-x-auto">
              <table className="rl-table min-w-[520px]">
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="font-bold text-rl-textStrong">{user.email}</td>
                      <td>{user.role}</td>
                      <td>{user.status}</td>
                      <td>
                        <button className="rl-button rl-button-secondary" type="button" onClick={() => revokeSessions(user.id)}>
                          <RotateCcw aria-hidden="true" size={16} />
                          Revoke sessions
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </form>
          <div className="rl-panel p-5">
            <h2 className="text-xl font-bold text-rl-textStrong">System Checks</h2>
            <div className="mt-3 grid gap-2">
              {checks.map((check) => (
                <div key={check.name} className="grid gap-2 border-b border-rl-line py-3 sm:grid-cols-[1fr_auto]">
                  <div>
                    <div className="font-bold text-rl-textStrong">{check.name}</div>
                    <div className="text-sm">{check.message}</div>
                  </div>
                  <StatusBadge status={check.status} />
                </div>
              ))}
            </div>
          </div>
          <form className="rl-panel grid gap-3 p-5" onSubmit={saveCompany}>
            <h2 className="text-xl font-bold text-rl-textStrong">Insurance Companies</h2>
            <input className="rl-input" placeholder="Company display name" value={companyName} onChange={(event) => setCompanyName(event.target.value)} required />
            <button className="rl-button w-fit" type="submit"><Save aria-hidden="true" size={18} />Save company</button>
          </form>
          <form className="rl-panel grid gap-3 p-5" onSubmit={saveTemplate}>
            <h2 className="text-xl font-bold text-rl-textStrong">Template Settings</h2>
            <input className="rl-input" placeholder="Template name" value={templateName} onChange={(event) => setTemplateName(event.target.value)} required />
            <button className="rl-button w-fit" type="submit"><Save aria-hidden="true" size={18} />Save template</button>
          </form>
          <form className="rl-panel grid gap-3 p-5" onSubmit={saveBenefit}>
            <h2 className="text-xl font-bold text-rl-textStrong">Benefits / Add-ons</h2>
            <input className="rl-input" placeholder="Benefit label" value={benefit} onChange={(event) => setBenefit(event.target.value)} required />
            <button className="rl-button w-fit" type="submit"><Save aria-hidden="true" size={18} />Save benefit</button>
          </form>
        </div>
      </section>
    </AppShell>
  );
}
