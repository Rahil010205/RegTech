import { PageTransition } from "@/components/shared/PageTransition";

export default function AuthTemplate({
  children,
}: {
  children: React.ReactNode;
}) {
  return <PageTransition>{children}</PageTransition>;
}
