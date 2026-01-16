// src/store/auth.store.ts
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { login, register, type User, type LoginRequest, type RegisterRequest } from "@/api/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (credentials) => {
        const response = await login(credentials);
        set({
          user: response.user,
          token: response.access_token,
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          isAuthenticated: true,
        });
      },

      register: async (data) => {
        await register(data);
        // After registration, automatically log in
        const loginResponse = await login({
          username: data.username,
          password: data.password,
        });
        set({
          user: loginResponse.user,
          token: loginResponse.access_token,
          accessToken: loginResponse.access_token,
          refreshToken: loginResponse.refresh_token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          token: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      setTokens: (access, refresh) => {
        set({ token: access, accessToken: access, refreshToken: refresh });
      },
    }),
    {
      name: "qa-auth-storage", // LocalStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Export as useAuthStore for compatibility
export const useAuthStore = useAuth;
