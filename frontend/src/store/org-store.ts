import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { OrganizationResponse, OrganizationCreateRequest } from "@/types/api";

interface OrgState {
  organizations: OrganizationResponse[];
  activeOrgId: string | null;
  setActiveOrg: (id: string) => void;
  loadOrganizations: () => Promise<void>;
  createOrganization: (payload: OrganizationCreateRequest) => Promise<OrganizationResponse>;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set, get) => ({
      organizations: [],
      activeOrgId: null,
      setActiveOrg: (id: string) => set({ activeOrgId: id }),
      loadOrganizations: async () => {
        try {
          const { listOrganizations } = await import("@/lib/api-client");
          const data = await listOrganizations();
          const orgsList: OrganizationResponse[] = Array.isArray(data)
            ? data
            : (data?.items ?? []);
          
          const currentActive = get().activeOrgId;
          const stillValid = currentActive && orgsList.some((o) => o.id === currentActive);
          
          set({
            organizations: orgsList,
            activeOrgId: stillValid ? currentActive : (orgsList[0]?.id ?? null),
          });
        } catch {
          // If backend unavailable in normal mode, keep local list
        }
      },
      createOrganization: async (payload: OrganizationCreateRequest) => {
        const { createOrganization } = await import("@/lib/api-client");
        const newOrg = await createOrganization(payload);
        set((state) => ({
          organizations: [...state.organizations, newOrg],
          activeOrgId: newOrg.id,
        }));
        return newOrg;
      },
    }),
    {
      name: "regtech-org-store",
      partialize: (state) => ({
        activeOrgId: state.activeOrgId,
        organizations: state.organizations,
      }),
    },
  ),
);
