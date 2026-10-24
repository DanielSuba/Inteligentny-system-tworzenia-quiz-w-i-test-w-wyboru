import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { register } from "@/api/auth";
import { FormPage } from "@/components/layout/FormPage";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { getSavedLocale } from "@/lib/locale";
import * as check from "@/lib/validate";

const empty = { email: "", username: "", displayName: "", pass: "", pass2: "" };

export function RegisterPage() {
  const { t } = useTranslation("auth");
  const [form, setForm] = useState(empty);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [sentTo, setSentTo] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (key: keyof typeof empty) => (e: { target: { value: string } }) =>
    setForm({ ...form, [key]: e.target.value });

  // sprawdza pola i zaklada konto
  async function submit(e: FormEvent) {
    e.preventDefault();
    const found = check.onlyErrors({
      email: check.email(form.email),
      username: check.username(form.username),
      pass: check.password(form.pass),
      pass2: check.same(form.pass, form.pass2),
    });
    setErrs(found);
    if (Object.keys(found).length) return;

    setBusy(true);
    setError("");
    try {
      await register({
        email: form.email.trim(),
        username: form.username.trim(),
        displayName: form.displayName.trim() || undefined,
        password: form.pass,
        locale: getSavedLocale(),
      });
      setSentTo(form.email.trim());
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  if (sentTo) {
    return (
      <FormPage title={t("register.title")}>
        <Notice kind="ok">{t("register.done", { email: sentTo })}</Notice>
      </FormPage>
    );
  }

  return (
    <FormPage
      title={t("register.title")}
      footer={
        <span>
          {t("register.haveAccount")}{" "}
          <Link to="/login" className="text-acc hover:underline">
            {t("login.submit")}
          </Link>
        </span>
      }
    >
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <Field
          label={t("fields.email")}
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={set("email")}
          error={errs.email && t(errs.email)}
        />
        <Field
          label={t("fields.username")}
          autoComplete="username"
          value={form.username}
          onChange={set("username")}
          hint={t("hints.username")}
          error={errs.username && t(errs.username)}
        />
        <Field
          label={t("fields.displayName")}
          value={form.displayName}
          maxLength={50}
          onChange={set("displayName")}
          hint={t("hints.displayName")}
        />
        <Field
          label={t("fields.password")}
          type="password"
          autoComplete="new-password"
          value={form.pass}
          onChange={set("pass")}
          hint={t("hints.password")}
          error={errs.pass && t(errs.pass)}
        />
        <Field
          label={t("fields.passwordRepeat")}
          type="password"
          autoComplete="new-password"
          value={form.pass2}
          onChange={set("pass2")}
          error={errs.pass2 && t(errs.pass2)}
        />
        {error && <Notice kind="error">{error}</Notice>}
        <Button type="submit" busy={busy}>
          {t("register.submit")}
        </Button>
      </form>
    </FormPage>
  );
}
