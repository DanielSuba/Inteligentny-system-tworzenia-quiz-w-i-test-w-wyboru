import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";

type Props = { codes: string[]; onDone: () => void };

// kody zapasowe pokazywane jeden raz: kopiowanie i pobranie jako plik tekstowy
export function BackupCodes({ codes, onDone }: Props) {
  const { t } = useTranslation("security");
  const [copied, setCopied] = useState(false);
  const text = codes.join("\n");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([`Apocrypha\n\n${text}\n`], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "apocrypha-kody-zapasowe.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col gap-3">
      <h3 className="font-bold">{t("twoFactor.codesTitle")}</h3>
      <Notice kind="info">{t("twoFactor.codesLead")}</Notice>
      <ul className="grid grid-cols-2 gap-2 font-pixel text-[16px] sm:grid-cols-5">
        {codes.map((c) => (
          <li key={c} className="border border-line bg-surf2 px-2 py-1.5 text-center">
            {c}
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={copy}>
          {copied ? t("twoFactor.copied") : t("twoFactor.copy")}
        </Button>
        <Button variant="secondary" onClick={download}>
          {t("twoFactor.download")}
        </Button>
        <Button onClick={onDone}>{t("twoFactor.saved")}</Button>
      </div>
    </div>
  );
}
