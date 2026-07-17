"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CircleHelp, KeyRound, Mail, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

type LoginStep = "email" | "code";

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<LoginStep>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  async function requestCode(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const result = await api<{ message: string }>("/auth/request-code", {
        method: "POST",
        body: JSON.stringify({ email })
      });
      setMessage(result.message);
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not request a login code.");
    } finally {
      setLoading(false);
    }
  }

  async function verifyCode(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api("/auth/verify-code", {
        method: "POST",
        body: JSON.stringify({ email, code })
      });
      router.replace("/upload");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not confirm the login code.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-rl-soft px-5 py-10">
      <section className="w-full max-w-md" aria-labelledby="login-title">
        <div className="mb-5 flex items-center gap-3 px-1">
          <div className="grid size-11 place-items-center rounded-md bg-rl-black text-white" aria-hidden="true">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-rl-red">Risklocker</p>
            <h1 id="login-title" className="text-2xl font-bold text-rl-textStrong">Quotation Converter</h1>
          </div>
        </div>

        <form className="rl-panel p-6 shadow-sm" onSubmit={step === "email" ? requestCode : verifyCode}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-rl-textStrong">{step === "email" ? "Employee sign in" : "Enter your code"}</h2>
              <p className="mt-1 text-sm">{step === "email" ? "Use your named employee email address." : `We sent a confirmation code for ${email}.`}</p>
            </div>
            <button
              className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-md px-2 text-sm font-bold text-rl-textStrong hover:bg-rl-soft"
              type="button"
              aria-expanded={showHelp}
              aria-controls="login-help"
              onClick={() => setShowHelp((current) => !current)}
            >
              <CircleHelp aria-hidden="true" size={17} />
              How to use
            </button>
          </div>

          {showHelp ? (
            <div id="login-help" className="mt-4 rounded-md border border-rl-line bg-rl-soft p-3 text-sm">
              Check the email provided for the login confirmation code.
            </div>
          ) : null}

          <div className="mt-6 grid gap-4">
            {step === "email" ? (
              <label className="grid gap-2 font-bold text-rl-textStrong">
                Employee email
                <span className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-rl-text" aria-hidden="true" size={18} />
                  <input
                    className="rl-input pl-10"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    aria-invalid={Boolean(error)}
                    required
                    autoFocus
                  />
                </span>
              </label>
            ) : (
              <label className="grid gap-2 font-bold text-rl-textStrong">
                Six-digit confirmation code
                <span className="relative">
                  <KeyRound className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-rl-text" aria-hidden="true" size={18} />
                  <input
                    className="rl-input pl-10 text-lg tracking-[0.3em]"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={code}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    aria-invalid={Boolean(error)}
                    required
                    autoFocus
                  />
                </span>
              </label>
            )}

            {message && !error ? <p className="rounded-md border border-rl-line bg-rl-soft p-3 text-sm">{message}</p> : null}
            {error ? <p role="alert" className="rounded-md border border-rl-red bg-red-50 p-3 font-bold text-rl-red">{error}</p> : null}

            <button className="rl-button w-full" disabled={loading} type="submit">
              {step === "email" ? <Mail aria-hidden="true" size={18} /> : <KeyRound aria-hidden="true" size={18} />}
              {loading ? (step === "email" ? "Sending code" : "Confirming code") : (step === "email" ? "Send login code" : "Confirm and sign in")}
            </button>

            {step === "code" ? (
              <button
                className="rl-button rl-button-secondary w-full"
                type="button"
                disabled={loading}
                onClick={() => {
                  setStep("email");
                  setCode("");
                  setMessage("");
                  setError("");
                }}
              >
                <ArrowLeft aria-hidden="true" size={18} />
                Use a different email
              </button>
            ) : null}
          </div>
        </form>
        <p className="mt-4 px-2 text-center text-sm">Private staff access. There is no public registration.</p>
      </section>
    </main>
  );
}
