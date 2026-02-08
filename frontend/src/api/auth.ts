import api from "./client";
import type { TokenPair, User } from "./types";

export async function register(
  username: string,
  email: string,
  password: string,
): Promise<User> {
  const { data } = await api.post<User>("/auth/register/", {
    username,
    email,
    password,
  });
  return data;
}

export async function login(
  username: string,
  password: string,
): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/auth/login/", {
    username,
    password,
  });
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  return data;
}

export async function refreshToken(refresh: string): Promise<{ access: string }> {
  const { data } = await api.post<{ access: string }>("/auth/refresh/", {
    refresh,
  });
  localStorage.setItem("access_token", data.access);
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me/");
  return data;
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
