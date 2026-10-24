import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { deleteAvatar, updateMe, uploadAvatar } from "@/api/me";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { useAuth } from "@/hooks/useAuth";
import { errorText } from "@/lib/errors";
import * as check from "@/lib/validate";

type Msg = { kind: "ok" | "error"; text: string } | null;

// profil: avatar, nazwy i opis
export function ProfilePage() {
  const { t } = useTranslation(["profile", "common", "auth"]);
  const { user, setUser } = useAuth();
  const me = user!;
  const fileRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    displayName: me.displayName,
    username: me.username,
    bio: me.bio,
  });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<Msg>(null);
  const [avatarMsg, setAvatarMsg] = useState<Msg>(null);
  const [busy, setBusy] = useState(false);

  // zapisuje zmiany profilu
  async function save(e: FormEvent) {
    e.preventDefault();
    const found = check.onlyErrors({
      displayName: check.required(form.displayName),
      username: check.username(form.username),
    });
    setErrs(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    try {
      setUser(await updateMe({ ...form, displayName: form.displayName.trim() }));
      setMsg({ kind: "ok", text: t("common:saved") });
    } catch (err) {
      setMsg({ kind: "error", text: errorText(err) });
    }
    setBusy(false);
  }

  // wgrywa wybrany plik jako avatar
  async function pickFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      setUser(await uploadAvatar(file));
      setAvatarMsg(null);
    } catch (err) {
      setAvatarMsg({ kind: "error", text: errorText(err) });
    }
  }

  async function removeAvatar() {
    setUser(await deleteAvatar().catch(() => me));
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-8">
      <section className="flex flex-col gap-4 border-t border-line pt-5">
        <h1 className="pixel uppercase">{t("title")}</h1>
        <div className="flex flex-wrap items-center gap-5">
          <Avatar url={me.avatarUrl} name={me.displayName} size={96} />
          <div className="flex flex-col gap-2">
            <p className="text-lg font-bold">{me.displayName}</p>
            <p className="pixel text-mut">@{me.username}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={pickFile} />
          <Button variant="secondary" onClick={() => fileRef.current?.click()}>
            <PixelIcon name="upload" scale={1} />
            {t("avatar.upload")}
          </Button>
          {me.avatarUrl && (
            <Button variant="ghost" onClick={removeAvatar}>
              {t("avatar.remove")}
            </Button>
          )}
        </div>
        <p className="text-sm text-mut">{t("avatar.hint")}</p>
        {avatarMsg && <Notice kind={avatarMsg.kind}>{avatarMsg.text}</Notice>}
      </section>

      <form onSubmit={save} noValidate className="flex flex-col gap-4 border-t border-line pt-5">
        <Field
          label={t("fields.displayName")}
          value={form.displayName}
          maxLength={50}
          onChange={(e) => setForm({ ...form, displayName: e.target.value })}
          error={errs.displayName && t(`auth:${errs.displayName}`)}
        />
        <Field
          label={t("fields.username")}
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          hint={t("auth:hints.username")}
          error={errs.username && t(`auth:${errs.username}`)}
        />
        <Field
          multiline
          label={t("fields.bio")}
          value={form.bio}
          maxLength={300}
          onChange={(e) => setForm({ ...form, bio: e.target.value })}
          hint={t("fields.bioHint")}
        />
        {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
        <Button type="submit" busy={busy} className="self-start">
          {t("common:save")}
        </Button>
      </form>
    </div>
  );
}
