import { NextResponse } from "next/server";
import { sendOtpEmail } from "@/lib/mailer";
import { issueOtp, normalizeEmail } from "@/lib/otp-server";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { email?: string };
    const email = normalizeEmail(body.email ?? "");
    const code = issueOtp(email);
    const delivery = await sendOtpEmail(email, code);
    if (delivery.sent) {
      return NextResponse.json({
        message: "A one-time password was sent to your email.",
        email_sent: true,
        dev_otp: null,
      });
    }
    return NextResponse.json({
      message:
        "A sign-in code was generated, but email is not configured. Add SMTP_HOST and SMTP_USER in frontend/.env.local to deliver codes to your inbox.",
      email_sent: false,
      dev_otp: code,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to send OTP.";
    const status = message.includes("wait") ? 429 : 400;
    return NextResponse.json({ message, email_sent: false }, { status });
  }
}
