import { LoginForm } from "@/components/shared/LoginForm";

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:48px_48px]" />
      <div className="relative z-10 flex w-full flex-col items-center gap-8">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.22em] text-zinc-500">
            Enterprise compliance
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            RegTech AI
          </h1>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
