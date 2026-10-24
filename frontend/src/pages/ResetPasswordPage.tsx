import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { resetPassword } from "@/api/auth";
import { FormPage } from "@/components/layout/FormPage";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import * as check from "@/lib/validate";

// otwierana z linku w e-mailu: ustawia nowe haslo
export function ResetPasswordPage() {
  const { t } = useTranslation("auth");
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [pass, setPass] = useState("");
  const [pass2, setPass2] = useState("");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [error, setError] = useState(token ? "" : t("verify.noToken"));
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const found = check.onlyErrors({ pass: check.password(pass), pass2: check.same(pass, pass2) });
    setErrs(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    setError("");
    try {
      await resetPassword(token, pass);
      setDone(true);
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  if (done) {
    return (
      <FormPage title={t("reset.title")}>
        <Notice kind="ok">{t("reset.done")}</Notice>
        <Link to="/login" className="text-acc hover:underline">
          {t("verify.toLogin")}
        </Link>
      </FormPage>
    );
  }

  return (
    <FormPage
      title={t("reset.title")}
      footer={
        <Link to="/forgot-password" className="hover:text-fg">
          {t("forgot.title")}
        </Link>
      }
    >
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <Field
          label={t("fields.newPassword")}
          type="password"
          autoComplete="new-password"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          hint={t("hints.password")}
          error={errs.pass && t(errs.pass)}
        />
        <Field
          label={t("fields.passwordRepeat")}
          type="password"
          autoComplete="new-password"
          value={pass2}
          onChange={(e) => setPass2(e.target.value)}
          error={errs.pass2 && t(errs.pass2)}
        />
        {error && <Notice kind="error">{error}</Notice>}
        <Button type="submit" busy={busy} disabled={!token}>
          {t("reset.submit")}
        </Button>
      </form>
    </FormPage>
  );
}
