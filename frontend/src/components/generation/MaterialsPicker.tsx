import { useRef, useState, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { addSourceUrl, deleteSource, uploadSource, type SourceDoc } from "@/api/generation";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { errorText } from "@/lib/errors";

type Props = {
  docs: SourceDoc[];
  selected: string[];
  onSelect: (ids: string[]) => void;
  onDocs: (docs: SourceDoc[]) => void;
};

// lista materialow z wyborem, wgrywanie pliku i dodawanie strony WWW
export function MaterialsPicker({ docs, selected, onSelect, onDocs }: Props) {
  const { t } = useTranslation("generate");
  const fileRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // nowy material od razu zaznaczony
  function added(doc: SourceDoc) {
    onDocs([doc, ...docs]);
    onSelect([...selected, doc.id]);
  }

  async function pickFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      added(await uploadSource(file));
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  async function addUrl() {
    setBusy(true);
    setError("");
    try {
      added(await addSourceUrl(url.trim()));
      setUrl("");
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  async function remove(id: string) {
    await deleteSource(id).catch(() => null);
    onDocs(docs.filter((d) => d.id !== id));
    onSelect(selected.filter((x) => x !== id));
  }

  const toggle = (id: string) =>
    onSelect(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  return (
    <div className="flex flex-col gap-4">
      <span className="text-sm text-mut">{t("source.docs")}</span>
      {docs.length === 0 ? (
        <p className="text-sm text-mut">{t("source.noDocs")}</p>
      ) : (
        <ul className="flex flex-col">
          {docs.map((d) => (
            <li
              key={d.id}
              className="flex items-center gap-3 border-b border-dashed border-line py-2"
            >
              <input
                type="checkbox"
                checked={selected.includes(d.id)}
                onChange={() => toggle(d.id)}
                aria-label={d.name}
                className="size-4 accent-[var(--acc)]"
              />
              <span className="min-w-0 flex-1">
                <span className="block truncate">{d.name}</span>
                <span className="text-sm text-mut">
                  {t("source.size", {
                    n: Math.max(1, Math.round(d.tokenCount / 1000)),
                    chunks: d.chunks,
                  })}
                </span>
              </span>
              <button onClick={() => remove(d.id)} className="text-sm text-mut hover:text-bad">
                {t("source.delete")}
              </button>
            </li>
          ))}
        </ul>
      )}

      <input
        ref={fileRef}
        type="file"
        hidden
        accept=".pdf,.docx,.pptx,.txt,.md"
        onChange={pickFile}
      />
      <div className="flex flex-col gap-1.5">
        <Button
          variant="secondary"
          className="self-start"
          busy={busy}
          onClick={() => fileRef.current?.click()}
        >
          <PixelIcon name="upload" scale={1} />
          {busy ? t("source.uploading") : t("source.upload")}
        </Button>
        <p className="text-sm text-mut">{t("source.uploadHint")}</p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Field
            label={t("source.url")}
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
        <Button variant="secondary" onClick={addUrl} busy={busy} disabled={!url.trim()}>
          {t("source.addUrl")}
        </Button>
      </div>
      {error && <Notice kind="error">{error}</Notice>}
    </div>
  );
}
