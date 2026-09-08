import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, UserRole } from "@/types/auth";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type OtpIssuer = "fastapi" | "next";

interface OtpRequestResult {
  message?: string;
  email_sent?: boolean;
  dev_otp?: string | null;
}

interface AuthState {
  user: User | null;
  token: string | null;
  otpPendingEmail: string | null;
  otpIssuer: OtpIssuer | null;
  emailSent: boolean;
  otpPreview: string | null;
  isAuthenticated: boolean;
  requestOtp: (email: string) => Promise<void>;
  verifyOtp: (otp: string) => Promise<void>;
  setRole: (role: UserRole) => void;
  logout: () => void;
}

async function postJson(url: string, body: unknown) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await response.json().catch(() => ({}))) as Record<
    string,
    unknown
  >;
  return { ok: response.ok, status: response.status, data };
}

function errorMessage(data: Record<string, unknown>, fallback: string) {
  if (typeof data.message === "string") return data.message;
  return fallback;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      otpPendingEmail: null,
      otpIssuer: null,
      emailSent: false,
      otpPreview: null,
      isAuthenticated: false,
      requestOtp: async (email: string) => {
        const normalized = email.trim().toLowerCase();

        const local = await postJson("/api/auth/otp/request", {
          email: normalized,
        });
        if (local.ok) {
          const result = local.data as OtpRequestResult;
          set({
            otpPendingEmail: normalized,
            otpIssuer: "next",
            emailSent: Boolean(result.email_sent),
            otpPreview: result.dev_otp ?? null,
          });
          return;
        }

        try {
          const backend = await postJson(`${API_BASE}/auth/otp/request`, {
            email: normalized,
          });
          if (backend.ok) {
            const result = backend.data as OtpRequestResult;
            set({
              otpPendingEmail: normalized,
              otpIssuer: "fastapi",
              emailSent: Boolean(result.email_sent),
              otpPreview: result.dev_otp ?? null,
            });
            return;
          }
          throw new Error(
            errorMessage(backend.data, "Unable to send OTP. Try again."),
          );
        } catch (error) {
          if (error instanceof Error && error.message !== "Failed to fetch") {
            throw error;
          }
          throw new Error(
            errorMessage(local.data, "Unable to send OTP. Try again."),
          );
        }
      },
      verifyOtp: async (otp: string) => {
        const email = get().otpPendingEmail;
        if (!email) {
          throw new Error("No OTP request in progress.");
        }
        if (!/^\d{6}$/.test(otp)) {
          throw new Error("Enter the 6-digit code.");
        }

        const issuer = get().otpIssuer;
        const endpoints =
          issuer === "fastapi"
            ? [`${API_BASE}/auth/otp/verify`, "/api/auth/otp/verify"]
            : ["/api/auth/otp/verify", `${API_BASE}/auth/otp/verify`];

        let lastError = "Invalid code.";
        for (const url of endpoints) {
          try {
            const response = await postJson(url, { email, otp });
            if (!response.ok) {
              lastError = errorMessage(response.data, lastError);
              continue;
            }
            const payload = response.data as {
              access_token?: string;
              user?: User;
            };
            if (!payload.access_token || !payload.user) {
              lastError = "Unexpected verify response.";
              continue;
            }
            set({
              user: payload.user,
              token: payload.access_token,
              otpPendingEmail: null,
              otpIssuer: null,
              emailSent: false,
              otpPreview: null,
              isAuthenticated: true,
            });
            return;
          } catch {
            lastError = "Unable to reach the authentication service.";
          }
        }
        throw new Error(lastError);
      },
      setRole: (role) => {
        const user = get().user;
        if (!user) return;
        set({ user: { ...user, role } });
      },
      logout: () =>
        set({
          user: null,
          token: null,
          otpPendingEmail: null,
          otpIssuer: null,
          emailSent: false,
          otpPreview: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "regtech-auth",
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
