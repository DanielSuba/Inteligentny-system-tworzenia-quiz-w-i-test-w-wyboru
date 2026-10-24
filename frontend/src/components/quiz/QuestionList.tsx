import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useTranslation } from "react-i18next";
import type { Question } from "@/api/quizzes";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { cn } from "@/lib/utils";

type Props = {
  questions: Question[];
  selected: string | null;
  newDraft: boolean;
  onSelect: (id: string) => void;
  onReorder: (ids: string[]) => void;
};

type RowProps = {
  q: Question;
  n: number;
  total: number;
  active: boolean;
  onSelect: () => void;
  onMove: (dir: -1 | 1) => void;
};

// jeden wiersz listy: uchwyt do przeciagania, numer, tresc, strzalki (telefon i klawiatura)
function Row({ q, n, total, active, onSelect, onMove }: RowProps) {
  const { t } = useTranslation("quiz");
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: q.id,
  });
  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-2 border-b border-dashed border-line bg-bg py-1.5",
        isDragging && "relative z-10 shadow-ring",
      )}
    >
      <button
        {...attributes}
        {...listeners}
        aria-label={t("editor.drag")}
        className="cursor-grab touch-none p-2 text-mut hover:text-fg"
      >
        <PixelIcon name="grip" scale={2} />
      </button>
      <button
        onClick={onSelect}
        aria-current={active || undefined}
        className={cn(
          "flex min-w-0 flex-1 items-baseline gap-2 py-1 text-left",
          active ? "text-acc" : "hover:text-fg",
        )}
      >
        <span className="font-pixel text-[12px] text-mut">{n}.</span>
        <span className="truncate">{q.text}</span>
      </button>
      <span className="flex shrink-0">
        <button
          onClick={() => onMove(-1)}
          disabled={n === 1}
          aria-label={t("editor.moveUp")}
          className="p-1.5 text-mut hover:text-fg disabled:opacity-30"
        >
          <PixelIcon name="up" scale={1} />
        </button>
        <button
          onClick={() => onMove(1)}
          disabled={n === total}
          aria-label={t("editor.moveDown")}
          className="p-1.5 text-mut hover:text-fg disabled:opacity-30"
        >
          <PixelIcon name="down" scale={1} />
        </button>
      </span>
    </li>
  );
}

// lista pytan z przeciaganiem (dnd-kit)
export function QuestionList({ questions, selected, newDraft, onSelect, onReorder }: Props) {
  const { t } = useTranslation("quiz");
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const ids = questions.map((q) => q.id);

  function dragEnd(e: DragEndEvent) {
    if (!e.over || e.active.id === e.over.id) return;
    const from = ids.indexOf(String(e.active.id));
    const to = ids.indexOf(String(e.over.id));
    onReorder(arrayMove(ids, from, to));
  }

  function move(i: number, dir: -1 | 1) {
    onReorder(arrayMove(ids, i, i + dir));
  }

  if (!questions.length && !newDraft) return <p className="text-mut">{t("editor.none")}</p>;

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={dragEnd}>
      <SortableContext items={ids} strategy={verticalListSortingStrategy}>
        <ol className="flex flex-col">
          {questions.map((q, i) => (
            <Row
              key={q.id}
              q={q}
              n={i + 1}
              total={questions.length}
              active={selected === q.id}
              onSelect={() => onSelect(q.id)}
              onMove={(dir) => move(i, dir)}
            />
          ))}
          {newDraft && (
            <li className="flex items-center gap-2 border-b border-dashed border-line py-2.5 pl-10 text-acc">
              {t("editor.newQuestion")}
              <span className="text-sm text-mut">({t("editor.unsaved")})</span>
            </li>
          )}
        </ol>
      </SortableContext>
    </DndContext>
  );
}
