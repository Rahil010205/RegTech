import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Organization } from "@/types/auth";

const MOCK_ORGANIZATIONS: Organization[] = [
  {
    id: "org-hdfc",
    name: "HDFC Bank",
    slug: "hdfc-bank",
    sector: "Banking",
  },
  {
    id: "org-icici",
    name: "ICICI Lombard",
    slug: "icici-lombard",
    sector: "Insurance",
  },
  {
    id: "org-zerodha",
    name: "Zerodha Broking",
    slug: "zerodha",
    sector: "Capital Markets",
  },
];

interface OrgState {
  organizations: Organization[];
  activeOrgId: string | null;
  setActiveOrg: (id: string) => void;
  activeOrganization: () => Organization | null;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set, get) => ({
      organizations: MOCK_ORGANIZATIONS,
      activeOrgId: MOCK_ORGANIZATIONS[0]?.id ?? null,
      setActiveOrg: (id) => set({ activeOrgId: id }),
      activeOrganization: () => {
        const { organizations, activeOrgId } = get();
        return organizations.find((org) => org.id === activeOrgId) ?? null;
      },
    }),
    {
      name: "regtech-org",
      partialize: (state) => ({
        activeOrgId: state.activeOrgId,
        organizations: state.organizations,
      }),
    },
  ),
);
