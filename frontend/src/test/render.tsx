import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import type { Me } from "@/api/me";
import { AuthContext, type AuthState } from "@/hooks/useAuth";

export const testUser: Me = {
  id: "1",
  email: "ania@example.com",
  emailVerified: true,
  role: "user",
  username: "ania",
  displayName: "Ania",
  avatarUrl: null,
  bio: "",
  locale: "pl",
  palette: "grafit",
};

// renderuje strone z routerem i podstawionym stanem logowania
export function renderPage(ui: ReactNode, user: Me | null = null, path = "/") {
  const auth: AuthState = { user, loading: false, setUser: vi.fn(), logout: vi.fn() };
  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </AuthContext.Provider>,
  );
  return auth;
}

// podstawia fetch zwracajacy podana odpowiedz
export function mockFetch(status: number, body: object) {
  const fn = vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}
