import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";

type Props = {
  lead?: string;
  label: string;
  submit: string;
  onSubmit: (code: string) => Promise<void>;
  onCancel?: () => void;
};

// male pole na kod 2FA (wlaczanie, wylaczanie, potwierdzenie zmiany)
export function CodePrompt({ lead, label, submit, onSubmit, onCancel }: Props) {
  const { t } = useTranslation("security");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    setBusy(true);
    setError("");
    try {
      await onSubmit(code.trim());
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  return (
    <form onSubmit={send} noValidate className="flex flex-col gap-3 border border-line bg-surf p-3">
      {lead && <p className="text-sm text-mut">{lead}</p>}
      <Field
        label={label}
        autoComplete="one-time-code"
        autoFocus
        maxLength={20}
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      {error && <Notice kind="error">{error}</Notice>}
      <div className="flex gap-2">
        <Button type="submit" busy={busy}>
          {submit}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            {t("twoFactor.cancel")}
          </Button>
        )}
      </div>
    </form>
  );
}
