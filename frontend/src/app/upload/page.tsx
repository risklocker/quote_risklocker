"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, Wand2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<FileList | null>(null);
  const [enhanced, setEnhanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!files?.length) return;
    setLoading(true);
    setError("");
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    form.append("enhanced_reading", String(enhanced));
    try {
      const result = await api<{ batch: { id: string } }>("/batches/upload", { method: "POST", body: form });
      router.push(`/batches/${result.batch.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <section className="grid gap-5">
        <div>
          <h1 className="text-3xl font-bold text-rl-textStrong">Upload Quotation PDFs</h1>
          <p className="mt-2 text-rl-text">Upload one or many quotation files. The system will show editable drafts after preparing quotations.</p>
        </div>
        <form className="rl-panel grid gap-5 p-5" onSubmit={submit}>
          <label className="grid min-h-48 cursor-pointer place-items-center rounded-md border-2 border-dashed border-rl-line bg-rl-soft p-6 text-center">
            <span className="grid justify-items-center gap-3">
              <Upload aria-hidden="true" size={28} />
              <span className="font-bold text-rl-textStrong">Choose PDF or image quotation files</span>
              <span className="text-sm">Up to 50 files, 50MB each</span>
            </span>
            <input className="sr-only" multiple accept=".pdf,.jfif,.jpg,.jpeg,.png,.tif,.tiff" type="file" onChange={(event) => setFiles(event.target.files)} />
          </label>
          {files?.length ? (
            <div className="rl-panel overflow-hidden">
              <table className="rl-table">
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Size</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from(files).map((file) => (
                    <tr key={`${file.name}-${file.size}`}>
                      <td>{file.name}</td>
                      <td>{Math.ceil(file.size / 1024)} KB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          <label className="flex items-center gap-3 font-bold text-rl-textStrong">
            <input className="h-5 w-5" type="checkbox" checked={enhanced} onChange={(event) => setEnhanced(event.target.checked)} />
            <Wand2 aria-hidden="true" size={18} />
            Use enhanced reading
          </label>
          {error ? <p className="rounded-md border border-rl-red bg-red-50 p-3 font-bold text-rl-red">{error}</p> : null}
          <button className="rl-button w-fit" disabled={loading || !files?.length} type="submit">
            <Upload aria-hidden="true" size={18} />
            {loading ? "Preparing quotations" : "Upload Quotation PDFs"}
          </button>
        </form>
      </section>
    </AppShell>
  );
}
