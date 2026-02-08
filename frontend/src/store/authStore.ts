import { create } from "zustand";
import type { User } from "@/api/types";
import * as authApi from "@/api/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  init: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"),
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      await authApi.login(username, password);
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true });
    try {
      await authApi.register(username, email, password);
      await authApi.login(username, password);
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    authApi.logout();
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  init: async () => {
    const token = localStorage.getItem("access_token");
    if (token) {
      set({ isLoading: true });
      try {
        const user = await authApi.getMe();
        set({ user, isAuthenticated: true });
      } catch {
        authApi.logout();
        set({ user: null, isAuthenticated: false });
      } finally {
        set({ isLoading: false });
      }
    }
  },
}));
