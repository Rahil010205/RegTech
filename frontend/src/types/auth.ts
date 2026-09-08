export type UserRole = "ADMIN" | "REGULATOR" | "ORGANIZATION";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatarUrl?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  sector: string;
}
