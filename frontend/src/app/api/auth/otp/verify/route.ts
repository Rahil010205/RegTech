import { NextResponse } from "next/server";
import { normalizeEmail, verifyIssuedOtp } from "@/lib/otp-server";
import type { User, UserRole } from "@/types/auth";

function userFromEmail(email: string): User {
  let role: UserRole = "ORGANIZATION";
  const local = email.split("@")[0] ?? "";
  if (local.includes("admin")) role = "ADMIN";
  else if (local.includes("regulator")) role = "REGULATOR";

  const name =
    role === "ADMIN"
      ? "Platform Admin"
      : role === "REGULATOR"
        ? "Regulatory Officer"
        : "Org Compliance Lead";

  return { id: crypto.randomUUID(), email, name, role };
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { email?: string; otp?: string };
    const email = normalizeEmail(body.email ?? "");
    const otp = (body.otp ?? "").trim();
    if (!/^\d{6}$/.test(otp)) {
      return NextResponse.json(
        { message: "Enter the 6-digit code." },
        { status: 400 },
      );
    }
    verifyIssuedOtp(email, otp);
    const user = userFromEmail(email);
    return NextResponse.json({
      access_token: `local.${Buffer.from(user.email).toString("base64url")}.${Date.now()}`,
      token_type: "bearer",
      user,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to verify OTP.";
    return NextResponse.json({ message }, { status: 401 });
  }
}
