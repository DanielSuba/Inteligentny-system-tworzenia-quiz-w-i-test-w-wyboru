import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from string import Template

PROMPTS = Path(__file__).resolve().parents[1] / "ai" / "prompts"
DIFFICULTY = {0: "mixed (easy, medium and hard)", 1: "easy", 2: "medium", 3: "hard"}
LANG = {"pl": ("Polish", "Prawda", "Fałsz"), "en": ("English", "True", "False")}


@dataclass
class GenRequest:
    count: int
    types: list[str]
    difficulty: int
    language: str
    focus: str = ""
    topic: str = ""


@lru_cache
def prompt(name: str) -> Template:
    return Template((PROMPTS / name).read_text(encoding="utf-8"))


@lru_cache
def examples(language: str) -> dict:
    return json.loads((PROMPTS / "examples" / f"{language}.json").read_text(encoding="utf-8"))


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@ Strategie @@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# wspolny interfejs strategii: nowa strategia (np. generator + krytyk w etapie 6) = nowa klasa
class Strategy(ABC):
    name: str
    version: str

    def system(self, req: GenRequest, withMaterial: bool) -> str:
        lang, yes, no = LANG[req.language]
        rule = (
            "sourceQuote: copy a short, VERBATIM fragment of the material that supports the answer."
            if withMaterial
            else "sourceQuote: leave empty (there is no material)."
        )
        return prompt("system.v1.md").substitute(
            language=lang,
            types=", ".join(req.types),
            difficulty=DIFFICULTY[req.difficulty],
            trueWord=yes,
            falseWord=no,
            sourceRule=rule,
            examples=self.examplesBlock(req),
        )

    @abstractmethod
    def examplesBlock(self, req: GenRequest) -> str: ...

    # wiadomosci dla modelu: z fragmentem materialu albo z samym tematem
    def messages(self, req: GenRequest, material: str | None) -> list[dict]:
        if material is not None:
            focus = f"Focus on: {req.focus}" if req.focus.strip() else ""
            user = prompt("material.v1.md").substitute(count=req.count, focus=focus, material=material)
        else:
            user = prompt("topic.v1.md").substitute(count=req.count, topic=req.topic)
        return [
            {"role": "system", "content": self.system(req, material is not None)},
            {"role": "user", "content": user},
        ]


class ZeroShot(Strategy):
    name, version = "zero_shot", "zero_shot.v1"

    def examplesBlock(self, req: GenRequest) -> str:
        return ""


# few-shot: 3 wzorcowe pytania (rozne typy) do przykladowego materialu
class FewShot(Strategy):
    name, version = "few_shot", "few_shot.v1"

    def examplesBlock(self, req: GenRequest) -> str:
        ex = examples(req.language)
        good = [q for q in ex["questions"] if q["type"] in req.types] or ex["questions"]
        return (
            "\nExample material:\n"
            + ex["material"]
            + "\n\nExample of good questions for it (JSON):\n"
            + json.dumps({"questions": good}, ensure_ascii=False, indent=1)
        )


STRATEGIES: dict[str, Strategy] = {"few_shot": FewShot(), "zero_shot": ZeroShot()}
