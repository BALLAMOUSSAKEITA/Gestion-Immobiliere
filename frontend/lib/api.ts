const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type HealthResponse = {
  status: string;
  version: string;
};

export type RoleSummary = {
  code: string;
  label: string;
};

export type AuthUserSummary = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUserSummary;
};

export type UserProfile = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  role: RoleSummary;
  is_active: boolean;
  last_login_at: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = "Une erreur est survenue";
    try {
      const data = await res.json();
      message = data.detail ?? message;
      if (Array.isArray(message)) {
        message = message.map((item) => item.msg ?? item).join(", ");
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(message, res.status);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  return parseResponse<T>(res);
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function loginRequest(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function refreshRequest(
  refreshToken: string,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export async function logoutRequest(
  accessToken: string,
  refreshToken: string,
): Promise<void> {
  await apiFetch<void>(
    "/api/v1/auth/logout",
    {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    },
    accessToken,
  );
}

export async function fetchMe(accessToken: string): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/v1/auth/me", {}, accessToken);
}

export async function changePasswordRequest(
  accessToken: string,
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await apiFetch<void>(
    "/api/v1/auth/change-password",
    {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    },
    accessToken,
  );
}

export function getDashboardPath(roleCode: string): string {
  if (roleCode === "locataire") return "/espace-locataire";
  if (roleCode === "visiteur") return "/annonces";
  return "/dashboard";
}

export type PermissionItem = {
  permission_code: string;
  granted: boolean;
  scope_type?: string | null;
  scope_id?: string | null;
};

export type UserSummary = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  role: RoleSummary;
  is_active: boolean;
  created_at: string;
};

export type UserDetail = UserSummary & {
  permissions: PermissionItem[];
  building_ids: string[];
  owner_profile_id: string | null;
  last_login_at: string | null;
};

export type UserListResponse = {
  items: UserSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type OwnerProfile = {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email: string | null;
  notes: string | null;
  user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateUserPayload = {
  email: string;
  password?: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role_code: string;
  is_active?: boolean;
  permissions?: PermissionItem[];
  building_ids?: string[];
  owner_profile_id?: string;
};

export async function fetchUsers(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<UserListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<UserListResponse>(`/api/v1/users${suffix}`, {}, accessToken);
}

export async function fetchUser(
  accessToken: string,
  userId: string,
): Promise<UserDetail> {
  return apiFetch<UserDetail>(`/api/v1/users/${userId}`, {}, accessToken);
}

export async function createUser(
  accessToken: string,
  payload: CreateUserPayload,
): Promise<UserDetail> {
  return apiFetch<UserDetail>(
    "/api/v1/users",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function updateUser(
  accessToken: string,
  userId: string,
  payload: Partial<CreateUserPayload>,
): Promise<UserDetail> {
  return apiFetch<UserDetail>(
    `/api/v1/users/${userId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function deactivateUser(
  accessToken: string,
  userId: string,
): Promise<void> {
  await apiFetch<void>(
    `/api/v1/users/${userId}`,
    { method: "DELETE" },
    accessToken,
  );
}

export async function resetUserPassword(
  accessToken: string,
  userId: string,
): Promise<{ temporary_password: string }> {
  return apiFetch<{ temporary_password: string }>(
    `/api/v1/users/${userId}/reset-password`,
    { method: "POST" },
    accessToken,
  );
}

export async function fetchUserPermissions(
  accessToken: string,
  userId: string,
): Promise<PermissionItem[]> {
  return apiFetch<PermissionItem[]>(
    `/api/v1/users/${userId}/permissions`,
    {},
    accessToken,
  );
}

export async function updateUserPermissions(
  accessToken: string,
  userId: string,
  permissions: PermissionItem[],
): Promise<PermissionItem[]> {
  return apiFetch<PermissionItem[]>(
    `/api/v1/users/${userId}/permissions`,
    { method: "PUT", body: JSON.stringify(permissions) },
    accessToken,
  );
}

export async function fetchOwnerProfiles(
  accessToken: string,
): Promise<{ items: OwnerProfile[] }> {
  return apiFetch<{ items: OwnerProfile[] }>(
    "/api/v1/owner-profiles",
    {},
    accessToken,
  );
}

export async function createOwnerProfile(
  accessToken: string,
  payload: {
    first_name: string;
    last_name: string;
    phone?: string;
    email?: string;
    notes?: string;
  },
): Promise<OwnerProfile> {
  return apiFetch<OwnerProfile>(
    "/api/v1/owner-profiles",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export const ROLE_OPTIONS = [
  { code: "super_admin", label: "Super Administrateur" },
  { code: "admin_familial", label: "Administrateur Familial" },
  { code: "proprietaire", label: "Propriétaire" },
  { code: "gestionnaire", label: "Gestionnaire" },
  { code: "visiteur", label: "Visiteur" },
  { code: "locataire", label: "Locataire" },
];

export const PERMISSION_LABELS: Record<string, string> = {
  "buildings.manage": "Gérer immeubles",
  "units.manage": "Gérer logements",
  "tenants.manage": "Gérer locataires",
  "payments.manage": "Gérer paiements",
  "expenses.manage": "Gérer dépenses",
  "repairs.manage": "Gérer réparations",
  "reports.read": "Consulter rapports",
  "documents.manage": "Gérer documents",
};

export type UnitType = "apartment" | "shop" | "office";
export type UnitStatus = "free" | "occupied" | "reserved" | "under_repair";

export const UNIT_TYPE_LABELS: Record<UnitType, string> = {
  apartment: "Appartement",
  shop: "Magasin",
  office: "Bureau",
};

export function formatCurrency(value: string | number): string {
  const amount = typeof value === "string" ? Number(value) : value;
  return `${new Intl.NumberFormat("fr-FR").format(amount)} FCFA`;
}

export type BuildingSummary = {
  id: string;
  code: string;
  name: string;
  address: string;
  commune: string;
  quartier: string | null;
  photo_url: string | null;
  floor_count: number;
  apartment_count: number;
  shop_count: number;
  owner_profile_id: string | null;
  manager_user_id: string | null;
  is_active: boolean;
  created_at: string;
};

export type BuildingDetail = BuildingSummary & {
  observations: string | null;
  total_units: number;
  occupied_units: number;
  free_units: number;
  under_repair_units: number;
  occupancy_rate: number;
  monthly_expected_rent: string;
  updated_at: string;
};

export type BuildingListResponse = {
  items: BuildingSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type BuildingCreatePayload = {
  name: string;
  address: string;
  commune: string;
  quartier?: string;
  floor_count?: number;
  owner_profile_id?: string;
  manager_user_id?: string;
  observations?: string;
};

export type UnitSummary = {
  id: string;
  building_id: string;
  code: string;
  type: UnitType;
  number: string;
  floor: number | null;
  rent_amount: string;
  deposit_amount: string;
  status: UnitStatus;
  is_public_listing: boolean;
  is_active: boolean;
  building_code?: string | null;
  building_name?: string | null;
  commune?: string | null;
  quartier?: string | null;
};

export type UnitDetail = UnitSummary & {
  description: string | null;
  photos: { id: string; url: string; is_primary: boolean }[];
  created_at: string;
  updated_at: string;
};

export type UnitListResponse = {
  items: UnitSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type UnitCreatePayload = {
  type: UnitType;
  number: string;
  floor?: number;
  rent_amount: string;
  deposit_amount?: string;
  description?: string;
  is_public_listing?: boolean;
};

export type PublicUnitSummary = {
  id: string;
  code: string;
  type: UnitType;
  rent_amount: string;
  deposit_amount: string;
  description: string | null;
  commune: string;
  quartier: string | null;
  primary_photo_url: string | null;
};

export type PublicUnitDetail = PublicUnitSummary & {
  photos: { id: string; url: string; is_primary: boolean }[];
};

export type PublicUnitListResponse = {
  items: PublicUnitSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export async function fetchBuildings(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<BuildingListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<BuildingListResponse>(
    `/api/v1/buildings${suffix}`,
    {},
    accessToken,
  );
}

export async function fetchBuilding(
  accessToken: string,
  buildingId: string,
): Promise<BuildingDetail> {
  return apiFetch<BuildingDetail>(
    `/api/v1/buildings/${buildingId}`,
    {},
    accessToken,
  );
}

export async function createBuilding(
  accessToken: string,
  payload: BuildingCreatePayload,
): Promise<BuildingDetail> {
  return apiFetch<BuildingDetail>(
    "/api/v1/buildings",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function updateBuilding(
  accessToken: string,
  buildingId: string,
  payload: Partial<BuildingCreatePayload> & { is_active?: boolean },
): Promise<BuildingDetail> {
  return apiFetch<BuildingDetail>(
    `/api/v1/buildings/${buildingId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchBuildingUnits(
  accessToken: string,
  buildingId: string,
): Promise<UnitListResponse> {
  return apiFetch<UnitListResponse>(
    `/api/v1/buildings/${buildingId}/units?page_size=100`,
    {},
    accessToken,
  );
}

export async function createBuildingUnit(
  accessToken: string,
  buildingId: string,
  payload: UnitCreatePayload,
): Promise<UnitDetail> {
  return apiFetch<UnitDetail>(
    `/api/v1/buildings/${buildingId}/units`,
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchUnits(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<UnitListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<UnitListResponse>(`/api/v1/units${suffix}`, {}, accessToken);
}

export async function fetchUnit(
  accessToken: string,
  unitId: string,
): Promise<UnitDetail> {
  return apiFetch<UnitDetail>(`/api/v1/units/${unitId}`, {}, accessToken);
}

export async function updateUnit(
  accessToken: string,
  unitId: string,
  payload: Partial<UnitCreatePayload & { status: UnitStatus; is_active: boolean }>,
): Promise<UnitDetail> {
  return apiFetch<UnitDetail>(
    `/api/v1/units/${unitId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchPublicUnits(
  params: Record<string, string | number | undefined> = {},
): Promise<PublicUnitListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<PublicUnitListResponse>(`/api/v1/public/units${suffix}`);
}

export async function fetchPublicUnit(unitId: string): Promise<PublicUnitDetail> {
  return apiFetch<PublicUnitDetail>(`/api/v1/public/units/${unitId}`);
}
