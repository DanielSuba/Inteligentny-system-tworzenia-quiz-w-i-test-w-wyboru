import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { resendVerification, verifyEmail } from "@/api/auth";
import { FormPage } from "@/components/layout/FormPage";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import * as check from "@/lib/validate";

type State = "wait" | "ok" | "error";

// otwierana z linku w e-mailu: potwierdza adres, przy bledzie pozwala wyslac nowy link
export function VerifyEmailPage() {
  const { t } = useTranslation("auth");
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [state, setState] = useState<State>(token ? "wait" : "error");
  const [error, setError] = useState(token ? "" : t("verify.noToken"));
  const [email, setEmail] = useState("");
  const [emailErr, setEmailErr] = useState("");
  const [resent, setResent] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    // token jest jednorazowy, wiec nie wysylamy go drugi raz (StrictMode)
    if (!token || started.current) return;
    started.current = true;
    verifyEmail(token)
      .then(() => setState("ok"))
      .catch((err) => {
        setState("error");
        setError(errorText(err));
      });
  }, [token]);

  async function resend(e: FormEvent) {
    e.preventDefault();
    const bad = check.email(email);
    setEmailErr(bad ? t(bad) : "");
    if (bad) return;
    await resendVerification(email.trim()).catch(() => null);
    setResent(true);
  }

  return (
    <FormPage title={t("verify.title")}>
      {state === "wait" && <p className="text-mut">{t("verify.wait")}</p>}
      {state === "ok" && (
        <>
          <Notice kind="ok">{t("verify.ok")}</Notice>
          <Link to="/login" className="text-acc hover:underline">
            {t("verify.toLogin")}
          </Link>
        </>
      )}
      {state === "error" && (
        <>
          <Notice kind="error">{error}</Notice>
          {resent ? (
            <Notice kind="ok">{t("login.resent")}</Notice>
          ) : (
            <form onSubmit={resend} noValidate className="flex flex-col gap-4">
              <Field
                label={t("verify.resendLead")}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={emailErr}
              />
              <Button type="submit" variant="secondary">
                {t("verify.resendSubmit")}
              </Button>
            </form>
          )}
        </>
      )}
    </FormPage>
  );
}
