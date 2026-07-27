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
