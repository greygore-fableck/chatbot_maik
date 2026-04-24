from dataclasses import dataclass
import re
from typing import Optional, Sequence


@dataclass(frozen=True)
class CompanyProfile:
    display_name: str
    aliases: tuple[str, ...]
    mention_response: str
    why_response: str


@dataclass(frozen=True)
class CompanyContextResult:
    company_key: Optional[str]
    intent: str
    text: str


COMPANY_INTENT_MENTION = "company_mention"
COMPANY_INTENT_WHY = "why_company"
COMPANY_INTENT_GENERAL_WHY = "general_why_company"

GENERAL_WHY_COMPANY_RESPONSE = (
    "Ich suche im Rahmen meiner Bachelorarbeit eine Praxisphase in einem digitalen Umfeld, "
    "in dem sich mein Thema sinnvoll mit realen digitalen Aufgaben verbinden lässt. "
    "Spannend wird es für mich dort, wo technische Umsetzung, Gestaltung und Nutzerperspektive "
    "nicht getrennt voneinander laufen."
)

COMPANY_PROFILES: dict[str, CompanyProfile] = {
    "deichmann": CompanyProfile(
        display_name="Deichmann",
        aliases=("deichmann",),
        mention_response=(
            "Deichmann ist für mich ein interessanter Kontext, weil digitale Anwendungen, "
            "Nutzerführung und Service dort sehr praktisch zusammenspielen. Genau diese "
            "Schnittstelle passt gut zu meinem Profil."
        ),
        why_response=(
            "Deichmann ist für mich interessant, weil dort digitale Anwendungen, Nutzerführung "
            "und Service konkret zusammenspielen. Genau an dieser Schnittstelle sehe ich mein "
            "Profil: Medieninformatik, Gestaltung, Web und Chatbot-Konzeption."
        ),
    ),
    "adesso": CompanyProfile(
        display_name="adesso",
        aliases=("adesso",),
        mention_response=(
            "adesso ist für mich interessant, weil ich mein Profil dort gut in digitale Projekte "
            "mit praktischem Bezug einbringen könnte: Gestaltung, Webentwicklung und digitale "
            "Konzeption."
        ),
        why_response=(
            "adesso ist für mich interessant, weil digitale Projekte dort mit praktischer "
            "Umsetzung zusammenkommen. Mein Profil passt an der Stelle gut: Gestaltung, "
            "Webentwicklung und nutzerorientierte digitale Konzeption."
        ),
    ),
    "materna": CompanyProfile(
        display_name="Materna",
        aliases=("materna",),
        mention_response=(
            "Materna ist für mich interessant, weil ich mein Profil dort gut in digitale Projekte "
            "mit praktischem Bezug einbringen könnte. Gerade die Verbindung aus Konzeption, "
            "technischer Umsetzung und Nutzerperspektive passt für mich gut dazu."
        ),
        why_response=(
            "Materna ist für mich interessant, weil ich mein Thema dort sinnvoll mit realen "
            "digitalen Aufgaben verbinden könnte. Mein Profil passt an der Stelle gut: "
            "Gestaltung, Webentwicklung, digitale Konzeption und die Arbeit an dialogischen "
            "Systemen."
        ),
    ),
}

WHY_TERMS = {"warum", "wieso", "weshalb"}
COMPANY_FIT_TERMS = {
    "bewerben",
    "bewerbung",
    "bewirbst",
    "bewerbe",
    "interessant",
    "passt",
    "passen",
    "profil",
    "reizt",
    "thema",
}
GENERAL_COMPANY_TARGETS = {
    "bei uns",
    "zu uns",
    "gerade wir",
    "genau wir",
    "dieses unternehmen",
    "unser unternehmen",
    "unternehmen",
    "firma",
    "hier",
}


def normalize_company_text(message: str) -> str:
    normalized = (message or "").casefold()
    normalized = (
        normalized.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _find_company_key(normalized: str) -> Optional[str]:
    padded = f" {normalized} "
    for key, profile in COMPANY_PROFILES.items():
        if any(f" {normalize_company_text(alias)} " in padded for alias in profile.aliases):
            return key
    return None


def _is_company_name_only(normalized: str, company_key: str) -> bool:
    profile = COMPANY_PROFILES[company_key]
    aliases = {normalize_company_text(alias) for alias in profile.aliases}
    return normalized in aliases


def _has_why_company_intent(normalized: str, company_key: Optional[str]) -> bool:
    words = set(normalized.split())
    has_why_term = bool(words & WHY_TERMS)
    has_fit_term = any(term in words for term in COMPANY_FIT_TERMS)
    has_general_target = any(target in normalized for target in GENERAL_COMPANY_TARGETS)

    if company_key:
        return has_why_term or has_fit_term

    return has_general_target and (has_why_term or has_fit_term)


def current_company_from_message(message: str) -> Optional[str]:
    normalized = normalize_company_text(message)
    if not normalized:
        return None
    return _find_company_key(normalized)


def current_company_from_conversation(history: Sequence[str]) -> Optional[str]:
    for previous_message in reversed(history):
        company_key = current_company_from_message(previous_message)
        if company_key is not None:
            return company_key
    return None


def resolve_company_context(
    message: str,
    history: Optional[Sequence[str]] = None,
) -> Optional[CompanyContextResult]:
    normalized = normalize_company_text(message)
    if not normalized:
        return None

    company_key = current_company_from_message(message)
    if company_key is None:
        company_key = current_company_from_conversation(history or [])
    has_why_intent = _has_why_company_intent(normalized, company_key)

    if current_company_from_message(message):
        profile = COMPANY_PROFILES[company_key]
        if has_why_intent and not _is_company_name_only(normalized, company_key):
            return CompanyContextResult(company_key, COMPANY_INTENT_WHY, profile.why_response)
        return CompanyContextResult(company_key, COMPANY_INTENT_MENTION, profile.mention_response)

    if company_key and has_why_intent:
        profile = COMPANY_PROFILES[company_key]
        return CompanyContextResult(company_key, COMPANY_INTENT_WHY, profile.why_response)

    if has_why_intent:
        return CompanyContextResult(None, COMPANY_INTENT_GENERAL_WHY, GENERAL_WHY_COMPANY_RESPONSE)

    return None


def build_company_context_response(
    message: str,
    history: Optional[Sequence[str]] = None,
) -> Optional[dict]:
    result = resolve_company_context(message, history=history)
    if result is None:
        return None

    return {
        "response": result.text,
        "messages": [
            {
                "text": result.text,
                "custom": {
                    "company_context": {
                        "company": result.company_key,
                        "intent": result.intent,
                    }
                },
            }
        ],
    }
