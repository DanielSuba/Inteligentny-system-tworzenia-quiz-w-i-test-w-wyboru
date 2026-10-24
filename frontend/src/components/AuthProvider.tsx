import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { logout as apiLogout } from "@/api/auth";
import { getMe, type Me } from "@/api/me";
import { AuthContext } from "@/hooks/useAuth";
import { setLocale } from "@/lib/locale";
import { setPalette } from "@/lib/palette";

// trzyma zalogowanego uzytkownika; przy starcie pyta backend o sesje
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  // ustawia uzytkownika i stosuje jego jezyk oraz palete
  const setUser = useCallback((next: Me | null) => {
    setUserState(next);
    if (next) {
      setLocale(next.locale);
      setPalette(next.palette);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getMe()
      .then((me) => active && setUser(me))
      .catch(() => active && setUserState(null))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [setUser]);

  const logout = useCallback(async () => {
    await apiLogout().catch(() => null);
    setUserState(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, setUser, logout }),
    [user, loading, setUser, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
