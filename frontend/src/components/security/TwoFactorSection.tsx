import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  disableTwoFactor,
  enableTwoFactor,
  newBackupCodes,
  setupTwoFactor,
  type Setup,
  type TwoFactorStatus,
} from "@/api/security";
import { BackupCodes } from "@/components/security/BackupCodes";
import { CodePrompt } from "@/components/security/CodePrompt";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { cn } from "@/lib/utils";

type Props = { status: TwoFactorStatus; onChanged: () => void };
type Mode = "idle" | "setup" | "codes" | "disable" | "regenerate";

// wlaczanie i wylaczanie 2FA, kody zapasowe
export function TwoFactorSection({ status, onChanged }: Props) {
  const { t } = useTranslation("security");
  const [mode, setMode] = useState<Mode>("idle");
  const [setup, setSetup] = useState<Setup | null>(null);
  const [codes, setCodes] = useState<string[]>([]);
  const [error, setError] = useState("");

  // krok 1: sekret i kod QR
  async function start() {
    setError("");
    try {
      setSetup(await setupTwoFactor());
      setMode("setup");
    } catch (e) {
      setError(errorText(e));
    }
  }

  function showCodes(list: string[]) {
    setCodes(list);
    setMode("codes");
    onChanged();
  }

  return (
    <section className="flex flex-col gap-4 border-t border-line pt-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="pixel uppercase">{t("twoFactor.title")}</h2>
        <span className={cn("pixel", status.enabled ? "text-ok" : "text-mut")}>
          {status.enabled ? t("twoFactor.on") : t("twoFactor.off")}
        </span>
      </div>
      <p className="text-mut">{t("twoFactor.lead")}</p>
      {error && <Notice kind="error">{error}</Notice>}

      {mode === "codes" && <BackupCodes codes={codes} onDone={() => setMode("idle")} />}

      {mode === "setup" && setup && (
        <div className="flex flex-col gap-3">
          <p className="text-sm">{t("twoFactor.scan")}</p>
          <div className="flex flex-wrap items-center gap-4">
            <img src={setup.qr} alt="QR" width={200} height={200} className="bg-white" />
            <code className="font-pixel text-[16px] break-all">{setup.secret}</code>
          </div>
          <CodePrompt
            label={t("twoFactor.code")}
            submit={t("twoFactor.confirm")}
            onSubmit={async (c) => showCodes((await enableTwoFactor(c)).codes)}
            onCancel={() => setMode("idle")}
          />
        </div>
      )}

      {mode === "idle" && !status.enabled && (
        <Button className="self-start" onClick={start}>
          {t("twoFactor.start")}
        </Button>
      )}

      {mode === "idle" && status.enabled && (
        <>
          <p className="text-sm">{t("twoFactor.backupLeft", { count: status.backupCodesLeft })}</p>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => setMode("regenerate")}>
              {t("twoFactor.regenerate")}
            </Button>
            <Button variant="ghost" className="hover:text-bad" onClick={() => setMode("disable")}>
              {t("twoFactor.disable")}
            </Button>
          </div>
        </>
      )}

      {(mode === "disable" || mode === "regenerate") && (
        <CodePrompt
          lead={mode === "disable" ? t("twoFactor.disable") : t("twoFactor.regenerate")}
          label={t("twoFactor.codeOrBackup")}
          submit={t("twoFactor.run")}
          onCancel={() => setMode("idle")}
          onSubmit={async (c) => {
            if (mode === "regenerate") return showCodes((await newBackupCodes(c)).codes);
            await disableTwoFactor(c);
            setMode("idle");
            onChanged();
          }}
        />
      )}
    </section>
  );
}
