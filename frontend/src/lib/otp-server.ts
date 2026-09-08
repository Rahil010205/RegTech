import { createHash, randomInt, timingSafeEqual } from "crypto";

export interface OtpRecord {
  digest: string;
  expiresAt: number;
  lastSentAt: number;
  attempts: number;
}

const globalStore = globalThis as typeof globalThis & {
  __regtechOtpStore?: Map<string, OtpRecord>;
};

function store() {
  if (!globalStore.__regtechOtpStore) {
    globalStore.__regtechOtpStore = new Map();
  }
  return globalStore.__regtechOtpStore;
}

const TTL_MS = 10 * 60 * 1000;
const RESEND_MS = 30 * 1000;
const SECRET = process.env.OTP_SECRET ?? "regtech-local-otp-secret";

export function normalizeEmail(email: string) {
  const value = email.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    throw new Error("Enter a valid work email.");
  }
  return value;
}

export function digestOtp(email: string, otp: string) {
  return createHash("sha256").update(`${email}:${otp}:${SECRET}`).digest("hex");
}

export function issueOtp(email: string) {
  const now = Date.now();
  const existing = store().get(email);
  if (existing && now - existing.lastSentAt < RESEND_MS) {
    const wait = Math.ceil((RESEND_MS - (now - existing.lastSentAt)) / 1000);
    throw new Error(`Please wait ${wait} seconds before requesting another code.`);
  }
  const otp = randomInt(0, 1_000_000).toString().padStart(6, "0");
  store().set(email, {
    digest: digestOtp(email, otp),
    expiresAt: now + TTL_MS,
    lastSentAt: now,
    attempts: 0,
  });
  return otp;
}

export function verifyIssuedOtp(email: string, otp: string) {
  const record = store().get(email);
  const now = Date.now();
  if (!record || now > record.expiresAt) {
    store().delete(email);
    throw new Error("That code is invalid or has expired.");
  }
  record.attempts += 1;
  if (record.attempts > 5) {
    store().delete(email);
    throw new Error("Too many attempts. Request a new code.");
  }
  const expected = Buffer.from(record.digest);
  const actual = Buffer.from(digestOtp(email, otp));
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) {
    throw new Error("That code is invalid or has expired.");
  }
  store().delete(email);
}
