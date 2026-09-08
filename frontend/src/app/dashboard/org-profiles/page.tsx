import { FeaturePage } from "@/components/shared/FeaturePage";

export default function OrgProfilesPage() {
  return (
    <FeaturePage
      title="Organization Profiles"
      description="View registered organization profiles, sectors, and onboarding status."
      allow={["ADMIN", "REGULATOR"]}
    />
  );
}
