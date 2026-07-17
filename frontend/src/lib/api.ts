"use client";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8100";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store"
  });
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "object" ? payload?.error?.message || "Something went wrong." : String(payload);
    throw new Error(message);
  }
  return payload as T;
}

export function fileUrl(path: string) {
  return `${API_BASE}${path}`;
}
