"use client";

import { useEffect, useState } from "react";
import { Check, Mail, MailOpen, Shield, UserCheck } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

type NotificationItem = {
  id: string;
  event_type: string;
  title: string;
  body: string;
  read_at: string | null;
  delivery_state: string;
  created_at: string;
};

const EVENT_ICONS: Record<string, typeof Mail> = {
  invitation: Mail,
  role_change: Shield,
  status_change: UserCheck,
};

function iconFor(event_type: string) {
  const Icon = EVENT_ICONS[event_type] || Mail;
  return <Icon aria-hidden="true" size={18} />;
}

export default function InboxPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [markingAll, setMarkingAll] = useState(false);
  const [marking, setMarking] = useState<Set<string>>(new Set());

  async function load() {
    setLoading(true);
    setError("");
    try {
      const result = await api<{ notifications: NotificationItem[] }>("/notifications");
      setNotifications(result.notifications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load notifications.");
    } finally {
      setLoading(false);
    }
  }

  async function markOneRead(id: string) {
    setMarking((prev) => new Set(prev).add(id));
    try {
      await api(`/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)),
      );
    } finally {
      setMarking((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  async function markAllRead() {
    setMarkingAll(true);
    try {
      await api("/notifications/read", { method: "PATCH" });
      const now = new Date().toISOString();
      setNotifications((prev) =>
        prev.map((n) => (n.read_at ? n : { ...n, read_at: now })),
      );
    } finally {
      setMarkingAll(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const unreadCount = notifications.filter((n) => !n.read_at).length;

  return (
    <AppShell>
      <section className="grid gap-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-rl-textStrong">Inbox</h1>
            <p className="mt-2">Account notifications, invitations, and role updates.</p>
          </div>
          {unreadCount > 0 && (
            <button
              className="rl-button rl-button-secondary"
              type="button"
              onClick={markAllRead}
              disabled={markingAll}
            >
              <Check aria-hidden="true" size={18} />
              {markingAll ? "Marking read..." : "Mark all read"}
            </button>
          )}
        </div>

        {error ? (
          <p role="alert" className="rounded-md border border-rl-red bg-red-50 p-3 font-bold text-rl-red">
            {error}
          </p>
        ) : null}

        {loading ? (
          <p className="font-bold text-rl-textStrong">Loading notifications...</p>
        ) : notifications.length === 0 ? (
          <div className="rl-panel p-8 text-center">
            <p className="font-bold text-rl-textStrong">No notifications yet.</p>
            <p className="mt-1">Invitations and account updates will appear here.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {notifications.map((item) => {
              const read = Boolean(item.read_at);
              return (
                <div
                  key={item.id}
                  className={`rl-panel flex items-start gap-4 p-4 ${read ? "" : "border-l-4 border-l-rl-black"}`}
                >
                  <span
                    className={`mt-0.5 flex-none rounded-md p-2 ${
                      read ? "text-rl-text bg-rl-soft" : "text-rl-inverse bg-rl-black"
                    }`}
                  >
                    {iconFor(item.event_type)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-rl-textStrong">
                        {item.title}
                      </span>
                      {item.delivery_state === "failed" && (
                        <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-bold text-rl-red">
                          Email delivery failed
                        </span>
                      )}
                    </div>
                    <p className="mt-1">{item.body}</p>
                    <p className="mt-1 text-sm text-rl-text">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!read ? (
                    <button
                      className="rl-button rl-button-secondary flex-none"
                      type="button"
                      onClick={() => markOneRead(item.id)}
                      disabled={marking.has(item.id)}
                      aria-label="Mark as read"
                    >
                      <MailOpen aria-hidden="true" size={18} />
                      <span className="hidden sm:inline">
                        {marking.has(item.id) ? "Marking..." : "Read"}
                      </span>
                    </button>
                  ) : (
                    <span className="flex-none p-2 text-rl-text" aria-label="Read">
                      <MailOpen aria-hidden="true" size={18} />
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </AppShell>
  );
}
