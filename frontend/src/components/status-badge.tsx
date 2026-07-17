type Status = "Ready" | "Check Needed" | "Cannot Read" | "Generated" | "Deleted" | "Preparing" | "Uploaded" | string;

const styles: Record<string, string> = {
  Ready: "border-rl-success text-rl-success bg-green-50",
  "Check Needed": "border-amber-500 text-rl-warning bg-amber-50",
  "Cannot Read": "border-rl-red text-rl-red bg-red-50",
  Generated: "border-rl-blue text-rl-blue bg-blue-50",
  Deleted: "border-zinc-500 text-zinc-700 bg-zinc-100",
  Preparing: "border-rl-blue text-rl-blue bg-blue-50",
  Uploaded: "border-zinc-400 text-zinc-700 bg-zinc-50"
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex min-h-7 items-center rounded-full border px-3 py-1 text-sm font-bold ${styles[status] || styles.Uploaded}`}>
      {status}
    </span>
  );
}
