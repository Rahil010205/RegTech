"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Loader2, Shield } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";

const spring = { type: "spring" as const, stiffness: 380, damping: 32 };

export function LoginForm() {
  const router = useRouter();
  const requestOtp = useAuthStore((s) => s.requestOtp);
  const verifyOtp = useAuthStore((s) => s.verifyOtp);
  const otpPendingEmail = useAuthStore((s) => s.otpPendingEmail);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const emailSent = useAuthStore((s) => s.emailSent);
  const otpPreview = useAuthStore((s) => s.otpPreview);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"email" | "otp">("email");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendOtp(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (!email.includes("@")) {
      setError("Enter a valid work email.");
      return;
    }
    setBusy(true);
    try {
      await requestOtp(email);
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send OTP.");
    } finally {
      setBusy(false);
    }
  }

  async function handleVerify(code: string) {
    if (code.length !== 6 || busy) return;
    setError(null);
    setBusy(true);
    try {
      await verifyOtp(code);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="w-full max-w-md overflow-hidden">
      <CardHeader className="space-y-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5">
          <Shield className="h-5 w-5" />
        </div>
        <div>
          <CardTitle className="text-xl">Sign in to RegTech AI</CardTitle>
          <CardDescription className="pt-1">
            We email a 6-digit code. No password required.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="relative min-h-[220px]">
        <AnimatePresence mode="wait">
          {step === "email" ? (
            <motion.form
              key="email"
              onSubmit={handleSendOtp}
              initial={{ x: 0, opacity: 1 }}
              exit={{ x: -48, opacity: 0 }}
              transition={spring}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="email">Work email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@organization.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Button type="submit" className="w-full" disabled={busy}>
                {busy && <Loader2 className="animate-spin" />}
                Send OTP
              </Button>
            </motion.form>
          ) : (
            <motion.div
              key="otp"
              initial={{ x: 48, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 48, opacity: 0 }}
              transition={spring}
              className="space-y-4"
            >
              <button
                type="button"
                onClick={() => {
                  setStep("email");
                  setOtp("");
                  setError(null);
                }}
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Use a different email
              </button>
              <div className="space-y-2">
                <Label>One-time passcode</Label>
                <p className="text-xs text-muted-foreground">
                  {emailSent
                    ? `Check ${otpPendingEmail ?? email} (and spam). The code expires in 10 minutes.`
                    : `Mail is not configured yet, so nothing was delivered to ${otpPendingEmail ?? email}.`}
                </p>
                {otpPreview && (
                  <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2">
                    <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                      Use this code
                    </p>
                    <p className="mt-1 font-mono text-2xl tracking-[0.35em]">
                      {otpPreview}
                    </p>
                    <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
                      To receive codes in your inbox, add SMTP settings to{" "}
                      <code>frontend/.env.local</code> (Gmail: smtp.gmail.com
                      and an App Password) and restart the dev server.
                    </p>
                  </div>
                )}
                <InputOTP
                  maxLength={6}
                  value={otp}
                  onChange={setOtp}
                  onComplete={handleVerify}
                  disabled={busy}
                >
                  <InputOTPGroup>
                    {Array.from({ length: 6 }).map((_, index) => (
                      <InputOTPSlot key={index} index={index} />
                    ))}
                  </InputOTPGroup>
                </InputOTP>
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Button
                className="w-full"
                disabled={busy || otp.length !== 6}
                onClick={() => handleVerify(otp)}
              >
                {busy && <Loader2 className="animate-spin" />}
                Verify and continue
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
