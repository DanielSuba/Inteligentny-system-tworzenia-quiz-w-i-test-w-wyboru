import { createContext, useContext } from "react";
import type { Me } from "@/api/me";

export type AuthState = {
  user: Me | null;
  loading: boolean;
  setUser: (user: Me | null) => void;
  logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthState | null>(null);

// dostep do zalogowanego uzytkownika w dowolnym komponencie
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth musi byc uzyte wewnatrz AuthProvider");
  return ctx;
}
