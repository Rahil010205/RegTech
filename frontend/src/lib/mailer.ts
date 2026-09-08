import nodemailer from "nodemailer";

export async function sendOtpEmail(to: string, code: string) {
  const host = process.env.SMTP_HOST?.trim();
  const from = (process.env.SMTP_FROM || process.env.SMTP_USER || "").trim();
  if (!host || !from) {
    return { sent: false as const, reason: "SMTP is not configured." };
  }

  const port = Number(process.env.SMTP_PORT ?? 587);
  const transporter = nodemailer.createTransport({
    host,
    port,
    secure: port === 465,
    auth:
      process.env.SMTP_USER && process.env.SMTP_PASS
        ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
        : undefined,
  });

  await transporter.sendMail({
    from,
    to,
    subject: "Your RegTech AI sign-in code",
    text: `Your RegTech AI one-time password is ${code}. It expires in 10 minutes.`,
    html: `
      <div style="font-family:Segoe UI,Arial,sans-serif;background:#09090b;color:#fafafa;padding:32px">
        <h1 style="font-size:18px;margin:0 0 12px">RegTech AI</h1>
        <p style="color:#a1a1aa;margin:0 0 20px">Use this one-time password to sign in.</p>
        <p style="letter-spacing:8px;font-size:28px;font-weight:600;margin:0 0 20px">${code}</p>
        <p style="color:#71717a;font-size:12px;margin:0">Expires in 10 minutes.</p>
      </div>
    `,
  });

  return { sent: true as const };
}
