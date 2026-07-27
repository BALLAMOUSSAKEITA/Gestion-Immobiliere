"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import {
  ApiError,
  changePasswordRequest,
  fetchMe,
  getDashboardPath,
  loginRequest,
  logoutRequest,
  refreshRequest,
  type UserProfile,
} from "@/lib/api";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "@/lib/auth-storage";

type AuthContextValue = {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const accessToken = getAccessToken();
    if (!accessToken) {
      setUser(null);
      return;
    }

    try {
      const profile = await fetchMe(accessToken);
      setUser(profile);
    } catch (error) {
      const refreshToken = getRefreshToken();
      if (error instanceof ApiError && error.status === 401 && refreshToken) {
        try {
          const tokens = await refreshRequest(refreshToken);
          setTokens(tokens.access_token, tokens.refresh_token);
          const profile = await fetchMe(tokens.access_token);
          setUser(profile);
          return;
        } catch {
          clearTokens();
          setUser(null);
          return;
        }
      }
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await loginRequest(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const profile = await fetchMe(tokens.access_token);
      setUser(profile);
      router.push(getDashboardPath(profile.role.code));
    },
    [router],
  );

  const logout = useCallback(async () => {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    if (accessToken && refreshToken) {
      try {
        await logoutRequest(accessToken, refreshToken);
      } catch {
        // ignore logout API errors locally
      }
    }
    clearTokens();
    setUser(null);
    router.push("/login");
  }, [router]);

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new ApiError("Authentification requise", 401);
      }
      await changePasswordRequest(accessToken, currentPassword, newPassword);
      clearTokens();
      setUser(null);
      router.push("/login");
    },
    [router],
  );

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      refreshUser,
      changePassword,
    }),
    [user, isLoading, login, logout, refreshUser, changePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth doit être utilisé dans un AuthProvider");
  }
  return context;
}
