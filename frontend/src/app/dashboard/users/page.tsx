import { FeaturePage } from "@/components/shared/FeaturePage";

export default function UsersPage() {
  return (
    <FeaturePage
      title="User Management"
      description="Provision users and assign Admin, Regulator, or Organization roles."
      allow={["ADMIN"]}
    />
  );
}
