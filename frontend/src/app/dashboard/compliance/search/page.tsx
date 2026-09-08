import { redirect } from "next/navigation";

// /dashboard/compliance/search → redirect to main compliance page
export default function ComplianceSearchPage() {
  redirect("/dashboard/compliance");
}
