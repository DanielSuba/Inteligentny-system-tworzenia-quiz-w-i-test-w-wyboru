import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getMe } from "@/api/me";
import {
  getAudit,
  getModels,
  getTwoFactor,
  listKeys,
  type ApiKey,
  type AuditEntry,
  type Model,
  type TwoFactorStatus,
} from "@/api/security";
import { SettingsTabs } from "@/components/layout/SettingsTabs";
import { ApiKeysSection } from "@/components/security/ApiKeysSection";
import { AuditSection, ModelsSection } from "@/components/security/InfoSections";
import { TwoFactorSection } from "@/components/security/TwoFactorSection";
import { Notice } from "@/components/ui/Notice";
import { useAuth } from "@/hooks/useAuth";
import { errorText } from "@/lib/errors";

type Data = { status: TwoFactorStatus; keys: ApiKey[]; models: Model[]; audit: AuditEntry[] };

// ustawienia bezpieczenstwa: 2FA, klucze API, modele, dziennik zdarzen
export function SecurityPage() {
  const { t } = useTranslation("security");
  const { setUser } = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");

  // pobiera wszystko od nowa po kazdej zmianie
  const load = useCallback(async () => {
    try {
      const [status, keys, models, audit] = await Promise.all([
        getTwoFactor(),
        listKeys(),
        getModels(),
        getAudit(),
      ]);
      setData({ status, keys, models, audit });
      setUser(await getMe());
    } catch (e) {
      setError(errorText(e));
    }
  }, [setUser]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8">
      <h1 className="pixel uppercase">{t("title")}</h1>
      <SettingsTabs />
      {error && <Notice kind="error">{error}</Notice>}
      {data && (
        <>
          <TwoFactorSection status={data.status} onChanged={load} />
          <ApiKeysSection keys={data.keys} twoFactor={data.status.enabled} onChanged={load} />
          <ModelsSection models={data.models} />
          <AuditSection entries={data.audit} />
        </>
      )}
    </div>
  );
}
