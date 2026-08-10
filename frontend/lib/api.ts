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
  "documents.read": "Consulter documents",
};

export type UnitType = "apartment" | "shop" | "office";
export type UnitStatus = "free" | "occupied" | "reserved" | "under_repair";

export const UNIT_TYPE_LABELS: Record<UnitType, string> = {
  apartment: "Appartement",
  shop: "Magasin",
  office: "Bureau",
};


export { formatCurrency, CURRENCY_CODE } from "./currency";

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

export async function deleteBuilding(
  accessToken: string,
  buildingId: string,
): Promise<void> {
  await apiFetch<void>(
    `/api/v1/buildings/${buildingId}`,
    { method: "DELETE" },
    accessToken,
  );
}

export async function uploadBuildingPhoto(
  accessToken: string,
  buildingId: string,
  file: File,
): Promise<BuildingDetail> {
  const formData = new FormData();
  formData.append("file", file);
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_URL}/api/v1/buildings/${buildingId}/photo`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse<BuildingDetail>(res);
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

export async function uploadUnitPhoto(
  accessToken: string,
  unitId: string,
  file: File,
): Promise<{ id: string; url: string; is_primary: boolean }> {
  const formData = new FormData();
  formData.append("file", file);
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_URL}/api/v1/units/${unitId}/photos`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse(res);
}

export async function deleteUnitPhoto(
  accessToken: string,
  unitId: string,
  photoId: string,
): Promise<void> {
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_URL}/api/v1/units/${unitId}/photos/${photoId}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new ApiError(await res.text(), res.status);
  }
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

export async function deleteUnit(accessToken: string, unitId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/units/${unitId}`, { method: "DELETE" }, accessToken);
}

export async function releaseUnit(
  accessToken: string,
  unitId: string,
  payload: { termination_reason?: string } = {},
): Promise<LeaseDetail> {
  return apiFetch<LeaseDetail>(
    `/api/v1/units/${unitId}/release`,
    { method: "POST", body: JSON.stringify(payload) },
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

export type IdDocumentType = "cni" | "passport" | "attestation" | "other";
export type PaymentMethod = "cash" | "orange_money" | "wave" | "bank_transfer";
export type LeaseStatus = "pending" | "active" | "expired" | "terminated";

export const ID_DOCUMENT_LABELS: Record<IdDocumentType, string> = {
  cni: "CNI",
  passport: "Passeport",
  attestation: "Attestation",
  other: "Autre",
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: "Espèces",
  orange_money: "Orange Money",
  wave: "Wave",
  bank_transfer: "Virement bancaire",
};

export const LEASE_STATUS_LABELS: Record<LeaseStatus, string> = {
  pending: "En attente",
  active: "Actif",
  expired: "Expiré",
  terminated: "Résilié",
};

export type TenantSummary = {
  id: string;
  first_name: string;
  last_name: string;
  phone_primary: string;
  profession: string | null;
  is_active: boolean;
  has_active_lease: boolean;
  current_unit_code: string | null;
  created_at: string;
};

export type TenantCurrentLease = {
  id: string;
  unit_code: string;
  building_name: string;
  rent_amount: string;
  start_date: string;
  status: string;
};

export type TenantDetail = TenantSummary & {
  phone_secondary: string | null;
  previous_address: string | null;
  id_document_type: IdDocumentType;
  id_document_number: string;
  id_document_url: string | null;
  photo_url: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  payment_method: PaymentMethod | null;
  observations: string | null;
  user_id: string | null;
  current_lease: TenantCurrentLease | null;
  active_leases?: TenantCurrentLease[];
  payment_summary: { total_paid: string; total_unpaid: string };
  updated_at: string;
};

export type TenantListResponse = {
  items: TenantSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type TenantCreatePayload = {
  first_name: string;
  last_name: string;
  phone_primary: string;
  phone_secondary?: string;
  profession?: string;
  previous_address?: string;
  id_document_type: IdDocumentType;
  id_document_number: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  payment_method?: PaymentMethod;
  observations?: string;
};

export type LeaseSummary = {
  id: string;
  tenant_id: string;
  tenant_name: string;
  unit_id: string;
  unit_code: string;
  building_name: string;
  start_date: string;
  end_date: string | null;
  rent_amount: string;
  deposit_amount: string;
  deposit_paid: boolean;
  status: LeaseStatus;
  created_at: string;
};

export type LeaseDetail = LeaseSummary & {
  contract_document_url: string | null;
  termination_date: string | null;
  termination_reason: string | null;
  updated_at: string;
};

export type LeaseListResponse = {
  items: LeaseSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type LeaseCreatePayload = {
  tenant_id: string;
  unit_id: string;
  start_date: string;
  end_date?: string;
  rent_amount: string;
  deposit_amount?: string;
  deposit_paid?: boolean;
};

export async function fetchTenants(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<TenantListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<TenantListResponse>(`/api/v1/tenants${suffix}`, {}, accessToken);
}

export async function fetchTenant(
  accessToken: string,
  tenantId: string,
): Promise<TenantDetail> {
  return apiFetch<TenantDetail>(`/api/v1/tenants/${tenantId}`, {}, accessToken);
}

export async function createTenant(
  accessToken: string,
  payload: TenantCreatePayload,
): Promise<TenantDetail> {
  return apiFetch<TenantDetail>(
    "/api/v1/tenants",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function deleteTenant(
  accessToken: string,
  tenantId: string,
): Promise<void> {
  await apiFetch<void>(
    `/api/v1/tenants/${tenantId}`,
    { method: "DELETE" },
    accessToken,
  );
}

export async function fetchLeases(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<LeaseListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<LeaseListResponse>(`/api/v1/leases${suffix}`, {}, accessToken);
}

export async function fetchLease(
  accessToken: string,
  leaseId: string,
): Promise<LeaseDetail> {
  return apiFetch<LeaseDetail>(`/api/v1/leases/${leaseId}`, {}, accessToken);
}

export async function createLease(
  accessToken: string,
  payload: LeaseCreatePayload,
): Promise<LeaseDetail> {
  return apiFetch<LeaseDetail>(
    "/api/v1/leases",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function terminateLease(
  accessToken: string,
  leaseId: string,
  payload: { termination_date: string; termination_reason: string },
): Promise<LeaseDetail> {
  return apiFetch<LeaseDetail>(
    `/api/v1/leases/${leaseId}/terminate`,
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchExpiringLeases(
  accessToken: string,
  days = 30,
): Promise<LeaseListResponse> {
  return apiFetch<LeaseListResponse>(
    `/api/v1/leases/expiring?days=${days}`,
    {},
    accessToken,
  );
}

export async function createTenantAccount(
  accessToken: string,
  tenantId: string,
  email: string,
): Promise<{ user_id: string; email: string; temporary_password: string | null }> {
  return apiFetch(
    `/api/v1/tenants/${tenantId}/create-account`,
    { method: "POST", body: JSON.stringify({ email }) },
    accessToken,
  );
}

export type PaymentStatus = "recorded" | "validated" | "cancelled";

export type RentPeriod = {
  id: string;
  period_year: number;
  period_month: number;
  expected_amount: string;
  paid_amount: string;
  remaining_amount: string;
  status: "pending" | "partial" | "paid" | "overdue";
  due_date: string;
};

export type PaymentSummary = {
  id: string;
  lease_id: string;
  tenant_id: string;
  tenant_name: string;
  unit_code: string;
  amount: string;
  payment_method: PaymentMethod;
  payment_date: string;
  reference: string | null;
  status: PaymentStatus;
  recorded_by_name: string;
  created_at: string;
  receipt_id: string | null;
  receipt_number: string | null;
};

export type PaymentDetail = PaymentSummary & {
  proof_url: string | null;
  notes: string | null;
  allocations: { period_year: number; period_month: number; allocated_amount: string }[];
  validated_by_name: string | null;
  validated_at: string | null;
  updated_at: string;
};

export type PaymentListResponse = {
  items: PaymentSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type PaymentCreatePayload = {
  lease_id: string;
  amount: string;
  payment_method: PaymentMethod;
  payment_date: string;
  reference?: string;
  notes?: string;
  allocations?: { period_year: number; period_month: number; amount: string }[];
};

export type ReceiptSummary = {
  id: string;
  payment_id: string;
  receipt_number: string;
  pdf_url: string;
  issued_at: string;
  issued_by_name: string;
  tenant_name: string;
  unit_code: string;
  amount: string;
  status: "issued" | "cancelled";
  sent_email_at: string | null;
};

export type ReceiptDetail = ReceiptSummary & {
  payment_date: string;
  payment_method: string;
};

export type ReceiptListResponse = {
  items: ReceiptSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export async function fetchLeasePeriods(
  accessToken: string,
  leaseId: string,
): Promise<RentPeriod[]> {
  return apiFetch<RentPeriod[]>(`/api/v1/leases/${leaseId}/periods`, {}, accessToken);
}

export async function fetchPayments(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaymentListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<PaymentListResponse>(`/api/v1/payments${suffix}`, {}, accessToken);
}

export async function fetchPayment(
  accessToken: string,
  paymentId: string,
): Promise<PaymentDetail> {
  return apiFetch<PaymentDetail>(`/api/v1/payments/${paymentId}`, {}, accessToken);
}

export async function createPayment(
  accessToken: string,
  payload: PaymentCreatePayload,
): Promise<PaymentDetail> {
  return apiFetch<PaymentDetail>(
    "/api/v1/payments",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchReceipts(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<ReceiptListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ReceiptListResponse>(`/api/v1/receipts${suffix}`, {}, accessToken);
}

export async function fetchReceipt(
  accessToken: string,
  receiptId: string,
): Promise<ReceiptDetail> {
  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${receiptId}`, {}, accessToken);
}

export async function sendReceiptEmail(
  accessToken: string,
  receiptId: string,
): Promise<{ message: string; sent_at: string }> {
  return apiFetch(`/api/v1/receipts/${receiptId}/send-email`, { method: "POST" }, accessToken);
}

export type OverdueItem = {
  id: string;
  tenant: { id: string; full_name: string; phone: string };
  unit_code: string;
  building_name: string;
  period: string;
  period_year: number;
  period_month: number;
  amount_due: string;
  amount_paid: string;
  amount_remaining: string;
  days_overdue: number;
  status: "open" | "partially_paid" | "resolved";
  tenant_total_overdue: string;
};

export type OverdueSummary = {
  total_overdue_amount: string;
  total_tenants_affected: number;
  total_periods_overdue: number;
};

export type OverdueListResponse = {
  items: OverdueItem[];
  summary: OverdueSummary;
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type TenantOverdueSummary = {
  tenant_id: string;
  tenant_name: string;
  phone: string;
  total_overdue_amount: string;
  overdue_months_count: number;
  oldest_overdue_days: number;
};

export async function fetchOverdues(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<OverdueListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<OverdueListResponse>(`/api/v1/overdues${suffix}`, {}, accessToken);
}

export async function fetchOverdue(
  accessToken: string,
  overdueId: string,
): Promise<OverdueItem> {
  return apiFetch<OverdueItem>(`/api/v1/overdues/${overdueId}`, {}, accessToken);
}

export async function fetchOverduesSummary(accessToken: string): Promise<OverdueSummary> {
  return apiFetch<OverdueSummary>("/api/v1/overdues/summary", {}, accessToken);
}

export async function fetchOverduesByTenant(
  accessToken: string,
): Promise<{ items: TenantOverdueSummary[] }> {
  return apiFetch<{ items: TenantOverdueSummary[] }>("/api/v1/overdues/by-tenant", {}, accessToken);
}

export type ExpenseCategory = {
  id: string;
  code: string;
  label: string;
  is_active: boolean;
};

export type ExpenseStatus = "recorded" | "pending_validation" | "validated" | "rejected";

export type ExpenseSummary = {
  id: string;
  category_code: string;
  category_label: string;
  building_name: string | null;
  unit_code: string | null;
  supplier_name: string | null;
  description: string;
  amount: string;
  payment_method: PaymentMethod;
  expense_date: string;
  status: ExpenseStatus;
  requires_validation: boolean;
  recorded_by_name: string;
  created_at: string;
};

export type ExpenseDetail = ExpenseSummary & {
  building_id: string | null;
  unit_id: string | null;
  owner_profile_id: string | null;
  receipt_url: string | null;
  validated_by_name: string | null;
  validated_at: string | null;
  updated_at: string;
};

export type ExpenseListResponse = {
  items: ExpenseSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type ExpenseSummaryStats = {
  total_amount: string;
  count: number;
  by_category: { category: string; amount: string; count: number }[];
};

export const EXPENSE_STATUS_LABELS: Record<ExpenseStatus, string> = {
  recorded: "Enregistrée",
  pending_validation: "En attente",
  validated: "Validée",
  rejected: "Rejetée",
};

export type ExpenseCreatePayload = {
  category_id: string;
  building_id?: string;
  unit_id?: string;
  owner_profile_id?: string;
  supplier_name?: string;
  description: string;
  amount: string;
  payment_method: PaymentMethod;
  expense_date: string;
};

export async function fetchExpenseCategories(accessToken: string): Promise<ExpenseCategory[]> {
  return apiFetch<ExpenseCategory[]>("/api/v1/expense-categories", {}, accessToken);
}

export async function fetchExpenses(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<ExpenseListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ExpenseListResponse>(`/api/v1/expenses${suffix}`, {}, accessToken);
}

export async function fetchExpense(
  accessToken: string,
  expenseId: string,
): Promise<ExpenseDetail> {
  return apiFetch<ExpenseDetail>(`/api/v1/expenses/${expenseId}`, {}, accessToken);
}

export async function fetchExpensesSummary(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<ExpenseSummaryStats> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ExpenseSummaryStats>(`/api/v1/expenses/summary${suffix}`, {}, accessToken);
}

export async function createExpense(
  accessToken: string,
  payload: ExpenseCreatePayload,
): Promise<ExpenseDetail> {
  return apiFetch<ExpenseDetail>(
    "/api/v1/expenses",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function validateExpense(
  accessToken: string,
  expenseId: string,
): Promise<ExpenseDetail> {
  return apiFetch<ExpenseDetail>(
    `/api/v1/expenses/${expenseId}/validate`,
    { method: "POST" },
    accessToken,
  );
}

export async function rejectExpense(
  accessToken: string,
  expenseId: string,
): Promise<ExpenseDetail> {
  return apiFetch<ExpenseDetail>(
    `/api/v1/expenses/${expenseId}/reject`,
    { method: "POST" },
    accessToken,
  );
}

export async function uploadExpenseReceipt(
  accessToken: string,
  expenseId: string,
  file: File,
): Promise<ExpenseDetail> {
  const formData = new FormData();
  formData.append("file", file);
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_URL}/api/v1/expenses/${expenseId}/receipt`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse<ExpenseDetail>(res);
}

export type RepairStatus =
  | "new"
  | "under_review"
  | "technician_assigned"
  | "in_progress"
  | "completed"
  | "cancelled";

export type UrgencyLevel = "low" | "medium" | "high";

export type RepairSummary = {
  id: string;
  title: string;
  unit_code: string;
  building_name: string;
  urgency: UrgencyLevel;
  status: RepairStatus;
  reported_by_name: string;
  assigned_to_name: string | null;
  reported_at: string;
  final_cost: string | null;
};

export type RepairDetail = RepairSummary & {
  unit_id: string;
  building_id: string;
  description: string;
  estimated_cost: string | null;
  expense_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  notes: string | null;
  attachments: {
    id: string;
    file_url: string;
    file_type: string;
    uploaded_by_name: string;
    uploaded_at: string;
  }[];
  updated_at: string;
};

export type RepairListResponse = {
  items: RepairSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type RepairSummaryStats = {
  in_progress_count: number;
  urgent_count: number;
  completed_this_month: number;
};

export type RepairHistoryItem = {
  id: string;
  old_status: string | null;
  new_status: string;
  changed_by_name: string;
  changed_at: string;
  comment: string | null;
};

export const REPAIR_STATUS_LABELS: Record<RepairStatus, string> = {
  new: "Nouvelle",
  under_review: "En analyse",
  technician_assigned: "Technicien affecté",
  in_progress: "En cours",
  completed: "Terminée",
  cancelled: "Annulée",
};

export const URGENCY_LABELS: Record<UrgencyLevel, string> = {
  low: "Faible",
  medium: "Moyen",
  high: "Élevé",
};

export type RepairCreatePayload = {
  unit_id?: string;
  title: string;
  description: string;
  urgency?: UrgencyLevel;
};

export async function fetchRepairs(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<RepairListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<RepairListResponse>(`/api/v1/repairs${suffix}`, {}, accessToken);
}

export async function fetchRepairsSummary(accessToken: string): Promise<RepairSummaryStats> {
  return apiFetch<RepairSummaryStats>("/api/v1/repairs/summary", {}, accessToken);
}

export async function fetchRepair(accessToken: string, repairId: string): Promise<RepairDetail> {
  return apiFetch<RepairDetail>(`/api/v1/repairs/${repairId}`, {}, accessToken);
}

export async function createRepair(
  accessToken: string,
  payload: RepairCreatePayload,
): Promise<RepairDetail> {
  return apiFetch<RepairDetail>(
    "/api/v1/repairs",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function updateRepairStatus(
  accessToken: string,
  repairId: string,
  payload: { status: RepairStatus; comment?: string },
): Promise<RepairDetail> {
  return apiFetch<RepairDetail>(
    `/api/v1/repairs/${repairId}/status`,
    { method: "PATCH", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function completeRepair(
  accessToken: string,
  repairId: string,
  payload: {
    final_cost: string;
    create_expense?: boolean;
    expense_category_id?: string;
    notes?: string;
  },
): Promise<RepairDetail> {
  return apiFetch<RepairDetail>(
    `/api/v1/repairs/${repairId}/complete`,
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function cancelRepair(
  accessToken: string,
  repairId: string,
  cancellation_reason: string,
): Promise<RepairDetail> {
  return apiFetch<RepairDetail>(
    `/api/v1/repairs/${repairId}/cancel`,
    { method: "POST", body: JSON.stringify({ cancellation_reason }) },
    accessToken,
  );
}

export async function fetchRepairHistory(
  accessToken: string,
  repairId: string,
): Promise<RepairHistoryItem[]> {
  return apiFetch<RepairHistoryItem[]>(`/api/v1/repairs/${repairId}/history`, {}, accessToken);
}

export async function uploadRepairAttachment(
  accessToken: string,
  repairId: string,
  file: File,
): Promise<RepairDetail> {
  const formData = new FormData();
  formData.append("file", file);
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_URL}/api/v1/repairs/${repairId}/attachments`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse<RepairDetail>(res);
}

export type DocumentEntityType =
  | "building"
  | "unit"
  | "tenant"
  | "lease"
  | "payment"
  | "expense"
  | "repair"
  | "owner_profile"
  | "receipt";

export type DocumentTypeItem = {
  id: string;
  code: string;
  label: string;
};

export type DocumentSummary = {
  id: string;
  document_type_code: string;
  document_type_label: string;
  title: string;
  description: string | null;
  file_name: string;
  file_size: number;
  mime_type: string;
  entity_type: DocumentEntityType;
  entity_id: string;
  uploaded_by_name: string;
  uploaded_at: string;
  is_archived: boolean;
  expires_at: string | null;
};

export type DocumentDetail = DocumentSummary & {
  file_url: string;
  updated_at: string;
};

export type DocumentListResponse = {
  items: DocumentSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type DocumentShareResponse = {
  id: string;
  share_token: string;
  share_url: string;
  expires_at: string;
  max_access: number;
  accessed_count: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDocumentTypes(accessToken: string): Promise<DocumentTypeItem[]> {
  return apiFetch<DocumentTypeItem[]>("/api/v1/document-types", {}, accessToken);
}

export async function fetchDocuments(
  accessToken: string,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<DocumentListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<DocumentListResponse>(`/api/v1/documents${suffix}`, {}, accessToken);
}

export async function fetchDocument(
  accessToken: string,
  documentId: string,
): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/api/v1/documents/${documentId}`, {}, accessToken);
}

export async function uploadDocument(
  accessToken: string,
  payload: {
    document_type_id: string;
    title: string;
    entity_type: DocumentEntityType;
    entity_id: string;
    description?: string;
    file: File;
  },
): Promise<DocumentDetail> {
  const formData = new FormData();
  formData.append("document_type_id", payload.document_type_id);
  formData.append("title", payload.title);
  formData.append("entity_type", payload.entity_type);
  formData.append("entity_id", payload.entity_id);
  if (payload.description) formData.append("description", payload.description);
  formData.append("file", payload.file);
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_BASE}/api/v1/documents`, {
    method: "POST",
    headers,
    body: formData,
  });
  return parseResponse<DocumentDetail>(res);
}

export function getDocumentDownloadUrl(documentId: string, accessToken: string): string {
  return `${API_BASE}/api/v1/documents/${documentId}/download?access_token=${accessToken}`;
}

export function getDocumentPreviewUrl(documentId: string, accessToken: string): string {
  return `${API_BASE}/api/v1/documents/${documentId}/preview`;
}

export async function shareDocument(
  accessToken: string,
  documentId: string,
  payload: { expires_in_days?: number; max_access?: number } = {},
): Promise<DocumentShareResponse> {
  return apiFetch<DocumentShareResponse>(
    `/api/v1/documents/${documentId}/share`,
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchSharedDocument(token: string): Promise<{
  title: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  download_url: string;
}> {
  return apiFetch(`/api/v1/documents/shared/${token}`);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

export type ApprovalRequestStatus = "pending" | "approved" | "rejected" | "cancelled";

export type ApprovalUserBrief = {
  id: string;
  full_name: string;
  email: string;
};

export type ApprovalRequestSummary = {
  id: string;
  action_code: string;
  entity_type: string;
  entity_id: string;
  status: ApprovalRequestStatus;
  reason: string;
  requested_by: ApprovalUserBrief;
  requested_at: string;
  reviewed_by: ApprovalUserBrief | null;
  reviewed_at: string | null;
  review_comment: string | null;
  executed_at: string | null;
};

export type ApprovalRequestDetail = ApprovalRequestSummary & {
  payload_before: Record<string, unknown> | null;
  payload_after: Record<string, unknown> | null;
};

export type ApprovalRequestListResponse = {
  items: ApprovalRequestSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export const APPROVAL_ACTION_LABELS: Record<string, string> = {
  "payment.delete": "Suppression paiement",
  "payment.update_amount": "Modification montant paiement",
  "tenant.delete": "Suppression locataire",
  "building.change_owner": "Changement propriétaire",
  "lease.update": "Modification contrat",
  "expense.validate": "Validation dépense",
  "receipt.cancel": "Annulation reçu",
  "document.delete": "Suppression document",
};

export const APPROVAL_STATUS_LABELS: Record<ApprovalRequestStatus, string> = {
  pending: "En attente",
  approved: "Approuvée",
  rejected: "Rejetée",
  cancelled: "Annulée",
};

export async function fetchApprovalRequests(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<ApprovalRequestListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ApprovalRequestListResponse>(
    `/api/v1/approval-requests${suffix}`,
    {},
    accessToken,
  );
}

export async function fetchMyApprovalRequests(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<ApprovalRequestListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ApprovalRequestListResponse>(
    `/api/v1/approval-requests/mine${suffix}`,
    {},
    accessToken,
  );
}

export async function fetchApprovalRequest(
  accessToken: string,
  requestId: string,
): Promise<ApprovalRequestDetail> {
  return apiFetch<ApprovalRequestDetail>(
    `/api/v1/approval-requests/${requestId}`,
    {},
    accessToken,
  );
}

export async function createApprovalRequest(
  accessToken: string,
  payload: {
    action_code: string;
    entity_type: string;
    entity_id: string;
    reason: string;
    payload_after?: Record<string, unknown> | null;
  },
): Promise<ApprovalRequestDetail> {
  return apiFetch<ApprovalRequestDetail>(
    "/api/v1/approval-requests",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function approveApprovalRequest(
  accessToken: string,
  requestId: string,
  reviewComment?: string,
): Promise<ApprovalRequestDetail> {
  return apiFetch<ApprovalRequestDetail>(
    `/api/v1/approval-requests/${requestId}/approve`,
    { method: "POST", body: JSON.stringify({ review_comment: reviewComment ?? null }) },
    accessToken,
  );
}

export async function rejectApprovalRequest(
  accessToken: string,
  requestId: string,
  reviewComment: string,
): Promise<ApprovalRequestDetail> {
  return apiFetch<ApprovalRequestDetail>(
    `/api/v1/approval-requests/${requestId}/reject`,
    { method: "POST", body: JSON.stringify({ review_comment: reviewComment }) },
    accessToken,
  );
}

export async function cancelApprovalRequest(
  accessToken: string,
  requestId: string,
): Promise<ApprovalRequestDetail> {
  return apiFetch<ApprovalRequestDetail>(
    `/api/v1/approval-requests/${requestId}/cancel`,
    { method: "POST" },
    accessToken,
  );
}

export async function deleteDocumentWithApproval(
  accessToken: string,
  documentId: string,
  reason?: string,
): Promise<ApprovalRequestDetail | void> {
  const query = reason ? `?reason=${encodeURIComponent(reason)}` : "";
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${API_BASE}/api/v1/documents/${documentId}${query}`, {
    method: "DELETE",
    headers,
  });
  if (res.status === 202) {
    return parseResponse<ApprovalRequestDetail>(res);
  }
  return parseResponse<void>(res);
}

export type AuditLogSummary = {
  id: string;
  user: ApprovalUserBrief;
  action: string;
  entity_type: string;
  entity_id: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  created_at: string;
};

export type AuditLogDetail = AuditLogSummary & {
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
};

export type AuditLogListResponse = {
  items: AuditLogSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export async function fetchAuditLogs(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<AuditLogListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<AuditLogListResponse>(`/api/v1/audit-logs${suffix}`, {}, accessToken);
}

export async function fetchAuditLog(
  accessToken: string,
  logId: string,
): Promise<AuditLogDetail> {
  return apiFetch<AuditLogDetail>(`/api/v1/audit-logs/${logId}`, {}, accessToken);
}

export async function fetchEntityAuditLogs(
  accessToken: string,
  entityType: string,
  entityId: string,
): Promise<AuditLogSummary[]> {
  return apiFetch<AuditLogSummary[]>(
    `/api/v1/audit-logs/entity/${entityType}/${entityId}`,
    {},
    accessToken,
  );
}

export type DashboardKpis = {
  total_buildings: number;
  total_apartments: number;
  total_shops: number;
  occupied_units: number;
  free_units: number;
  expected_rent_month: number | null;
  collected_rent_month: number | null;
  overdue_amount: number;
  expenses_month: number | null;
  net_profit_month: number | null;
  expiring_leases_count: number;
  repairs_in_progress: number;
  show_financials: boolean;
};

export type MonthlySeriesPoint = {
  label: string;
  year: number;
  month: number;
  revenue: number;
  expenses: number;
  net_profit: number;
};

export type DashboardAlert = {
  type: string;
  severity: string;
  title: string;
  message: string;
  href: string | null;
};

export type ReportSummary = {
  id: string;
  report_type: string;
  period_start: string;
  period_end: string;
  filters: Record<string, unknown> | null;
  pdf_url: string | null;
  excel_url: string | null;
  generated_by_name: string | null;
  generated_at: string;
};

export type ReportDetail = ReportSummary & { data: Record<string, unknown> };

export async function fetchDashboardKpis(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<DashboardKpis> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<DashboardKpis>(`/api/v1/dashboard/kpis${suffix}`, {}, accessToken);
}

export async function fetchRevenueExpenseChart(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<{ points: MonthlySeriesPoint[] }> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch(`/api/v1/dashboard/charts/revenue-expenses${suffix}`, {}, accessToken);
}

export async function fetchOccupancyChart(
  accessToken: string,
  params: Record<string, string | number | undefined> = {},
): Promise<{ points: { label: string; occupancy_rate: number }[] }> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch(`/api/v1/dashboard/charts/occupancy${suffix}`, {}, accessToken);
}

export async function fetchDashboardAlerts(accessToken: string): Promise<{ items: DashboardAlert[] }> {
  return apiFetch("/api/v1/dashboard/alerts", {}, accessToken);
}

export async function fetchDashboardTopOverdues(accessToken: string): Promise<{
  items: { tenant_name: string; unit_code: string; amount_remaining: number; days_overdue: number }[];
}> {
  return apiFetch("/api/v1/dashboard/top-overdues", {}, accessToken);
}

export async function fetchDashboardExpiringLeases(accessToken: string): Promise<{
  items: {
    lease_id: string;
    tenant_name: string;
    unit_code: string;
    building_name: string;
    end_date: string;
    days_remaining: number;
  }[];
}> {
  return apiFetch("/api/v1/dashboard/expiring-leases", {}, accessToken);
}

export async function fetchReports(
  accessToken: string,
  page = 1,
): Promise<{ items: ReportSummary[]; total: number }> {
  return apiFetch(`/api/v1/reports?page=${page}`, {}, accessToken);
}

export async function fetchReport(accessToken: string, reportId: string): Promise<ReportDetail> {
  return apiFetch(`/api/v1/reports/${reportId}`, {}, accessToken);
}

export async function generateReport(
  accessToken: string,
  payload: {
    report_type: string;
    period_start: string;
    period_end: string;
    export_formats?: string[];
    filters?: {
      building_id?: string;
      owner_profile_id?: string;
      tenant_id?: string;
      manager_user_id?: string;
      unit_type?: string;
    };
  },
): Promise<ReportDetail> {
  return apiFetch(
    "/api/v1/reports/generate",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export function getReportDownloadUrl(reportId: string, format: "pdf" | "excel"): string {
  return `/api/v1/reports/${reportId}/${format}`;
}

export type VisitRequestSummary = {
  id: string;
  unit_id: string;
  unit_code: string;
  visitor_name: string;
  visitor_email: string;
  visitor_phone: string;
  preferred_date: string | null;
  preferred_time: string | null;
  message: string | null;
  status: string;
  assigned_to_name: string | null;
  created_at: string;
};

export type VisitRequestListResponse = {
  items: VisitRequestSummary[];
  total: number;
};

export type PortalMessageSummary = {
  id: string;
  sender_name: string;
  sender_email: string;
  subject: string;
  body: string;
  is_read: boolean;
  created_at: string;
  parent_message_id: string | null;
};

export type PortalMessageListResponse = {
  items: PortalMessageSummary[];
  total: number;
};

export type TenantPortalDashboard = {
  tenant: { full_name: string };
  unit: { code: string; type: string } | null;
  lease: { rent_amount: number; end_date: string | null } | null;
  payment_status: {
    current_month_paid: boolean;
    total_unpaid: number;
    next_due_date: string | null;
  };
  unread_notices: number;
  active_repairs: number;
  has_active_lease: boolean;
};

export type TenantUnitInfo = {
  id: string;
  code: string;
  type: string;
  number: string;
  rent_amount: number;
  building_name: string;
  commune: string;
  quartier: string | null;
  description: string | null;
  photos: { id: string; url: string }[];
};

export type TenantLeaseInfo = {
  id: string;
  start_date: string;
  end_date: string | null;
  rent_amount: number;
  deposit_amount: number;
  status: string;
  contract_document_url: string | null;
};

export type TenantNoticeSummary = {
  id: string;
  title: string;
  content: string | null;
  notice_type: string;
  published_at: string;
  is_read: boolean;
};

export type TenantDocumentItem = {
  id: string;
  title: string;
  file_name: string;
  mime_type: string;
  uploaded_at: string;
};

export async function createVisitRequest(payload: {
  unit_id: string;
  visitor_name: string;
  visitor_email: string;
  visitor_phone: string;
  preferred_date?: string;
  preferred_time?: string;
  message?: string;
}): Promise<VisitRequestSummary> {
  return apiFetch<VisitRequestSummary>("/api/v1/public/visit-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createPublicContact(payload: {
  sender_name: string;
  sender_email: string;
  sender_phone?: string;
  unit_id?: string;
  subject: string;
  body: string;
}): Promise<PortalMessageSummary> {
  return apiFetch<PortalMessageSummary>("/api/v1/public/contact", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchVisitRequests(accessToken: string): Promise<VisitRequestListResponse> {
  return apiFetch<VisitRequestListResponse>("/api/v1/visit-requests", {}, accessToken);
}

export async function updateVisitRequest(
  accessToken: string,
  requestId: string,
  payload: { status?: string; assigned_to?: string },
): Promise<VisitRequestSummary> {
  return apiFetch<VisitRequestSummary>(
    `/api/v1/visit-requests/${requestId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchTenantDashboard(accessToken: string): Promise<TenantPortalDashboard> {
  return apiFetch<TenantPortalDashboard>("/api/v1/tenant-portal/dashboard", {}, accessToken);
}

export async function fetchTenantUnit(accessToken: string): Promise<TenantUnitInfo> {
  return apiFetch<TenantUnitInfo>("/api/v1/tenant-portal/my-unit", {}, accessToken);
}

export async function fetchTenantLease(accessToken: string): Promise<TenantLeaseInfo> {
  return apiFetch<TenantLeaseInfo>("/api/v1/tenant-portal/my-lease", {}, accessToken);
}

export async function fetchTenantPayments(accessToken: string): Promise<PaymentListResponse> {
  return apiFetch<PaymentListResponse>("/api/v1/tenant-portal/payments", {}, accessToken);
}

export async function fetchTenantReceipts(accessToken: string): Promise<ReceiptListResponse> {
  return apiFetch<ReceiptListResponse>("/api/v1/tenant-portal/receipts", {}, accessToken);
}

export async function fetchTenantDocuments(
  accessToken: string,
): Promise<{ items: TenantDocumentItem[] }> {
  return apiFetch<{ items: TenantDocumentItem[] }>(
    "/api/v1/tenant-portal/documents",
    {},
    accessToken,
  );
}

export async function fetchTenantNotices(accessToken: string): Promise<TenantNoticeSummary[]> {
  return apiFetch<TenantNoticeSummary[]>("/api/v1/tenant-portal/notices", {}, accessToken);
}

export async function fetchTenantMessages(accessToken: string): Promise<PortalMessageListResponse> {
  return apiFetch<PortalMessageListResponse>(
    "/api/v1/tenant-portal/messages",
    {},
    accessToken,
  );
}

export async function sendTenantMessage(
  accessToken: string,
  payload: { subject: string; body: string; unit_id?: string },
): Promise<PortalMessageSummary> {
  return apiFetch<PortalMessageSummary>(
    "/api/v1/tenant-portal/messages",
    { method: "POST", body: JSON.stringify(payload) },
    accessToken,
  );
}

export async function fetchManagerMessages(accessToken: string): Promise<PortalMessageListResponse> {
  return apiFetch<PortalMessageListResponse>("/api/v1/messages", {}, accessToken);
}

export async function replyToMessage(
  accessToken: string,
  messageId: string,
  body: string,
): Promise<PortalMessageSummary> {
  return apiFetch<PortalMessageSummary>(
    `/api/v1/messages/${messageId}/reply`,
    { method: "POST", body: JSON.stringify({ body }) },
    accessToken,
  );
}

export type NotificationSummary = {
  id: string;
  event_code: string;
  title: string;
  body: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: NotificationSummary[];
  total: number;
  unread_count: number;
};

export type NotificationPreferenceItem = {
  event_code: string;
  label: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  whatsapp_enabled: boolean;
};

export async function fetchNotifications(
  accessToken: string,
  limit = 50,
): Promise<NotificationListResponse> {
  return apiFetch<NotificationListResponse>(
    `/api/v1/notifications?limit=${limit}`,
    {},
    accessToken,
  );
}

export async function fetchUnreadNotificationCount(
  accessToken: string,
): Promise<{ count: number }> {
  return apiFetch<{ count: number }>("/api/v1/notifications/unread-count", {}, accessToken);
}

export async function markNotificationRead(
  accessToken: string,
  notificationId: string,
): Promise<NotificationSummary> {
  return apiFetch<NotificationSummary>(
    `/api/v1/notifications/${notificationId}/read`,
    { method: "PATCH" },
    accessToken,
  );
}

export async function markAllNotificationsRead(accessToken: string): Promise<{ marked: number }> {
  return apiFetch<{ marked: number }>(
    "/api/v1/notifications/read-all",
    { method: "POST" },
    accessToken,
  );
}

export async function fetchNotificationPreferences(
  accessToken: string,
): Promise<{ items: NotificationPreferenceItem[] }> {
  return apiFetch<{ items: NotificationPreferenceItem[] }>(
    "/api/v1/notification-preferences",
    {},
    accessToken,
  );
}

export async function updateNotificationPreferences(
  accessToken: string,
  preferences: Array<{
    event_code: string;
    in_app_enabled?: boolean;
    email_enabled?: boolean;
    whatsapp_enabled?: boolean;
  }>,
): Promise<{ items: NotificationPreferenceItem[] }> {
  return apiFetch<{ items: NotificationPreferenceItem[] }>(
    "/api/v1/notification-preferences",
    { method: "PUT", body: JSON.stringify({ preferences }) },
    accessToken,
  );
}

export async function getReceiptWhatsAppLink(
  accessToken: string,
  receiptId: string,
): Promise<{ url: string; message: string }> {
  return apiFetch<{ url: string; message: string }>(
    `/api/v1/receipts/${receiptId}/send-whatsapp`,
    { method: "POST" },
    accessToken,
  );
}

export type UnitHistoryItem = {
  id: string;
  tenant_id: string | null;
  tenant_name: string | null;
  entry_date: string;
  exit_date: string | null;
  rent_amount: string;
  notes: string | null;
};

export async function fetchUnitHistory(
  accessToken: string,
  unitId: string,
): Promise<UnitHistoryItem[]> {
  return apiFetch<UnitHistoryItem[]>(`/api/v1/units/${unitId}/history`, {}, accessToken);
}
