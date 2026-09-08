import { RoleGuard } from "@/components/shared/RoleGuard";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { UserRole } from "@/types/auth";

export function FeaturePage({
  title,
  description,
  allow,
}: {
  title: string;
  description: string;
  allow: UserRole[];
}) {
  return (
    <RoleGuard allow={allow}>
      <div className="mx-auto max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{title}</CardTitle>
            <CardDescription className="text-sm">{description}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    </RoleGuard>
  );
}
