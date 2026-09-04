from dataclasses import dataclass
import re
from typing import Optional, Sequence


@dataclass(frozen=True)
class CompanyProfile:
    display_name: str
    aliases: tuple[str, ...]
    mention_response: str
    why_response: str
    fit_response: str


@dataclass(frozen=True)
class CompanyContextResult:
    company_key: Optional[str]
    intent: str
    text: str


COMPANY_INTENT_MENTION = "company_mention"
COMPANY_INTENT_WHY = "why_company"
COMPANY_INTENT_FIT = "fit_company"
COMPANY_INTENT_GENERAL_WHY = "general_why_company"

GENERAL_WHY_COMPANY_RESPONSE = (
    "Ich suche im Rahmen meiner Bachelorarbeit eine Praxisphase in einem digitalen Umfeld, "
    "in dem sich mein Thema sinnvoll mit realen digitalen Aufgaben verbinden lässt. "
    "Spannend wird es für mich dort, wo technische Umsetzung, Gestaltung und Nutzerperspektive "
    "nicht getrennt voneinander laufen."
)

COMPANY_PROFILES: dict[str, CompanyProfile] = {
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
            "Umsetzung zusammenkommen und nutzerorientiert gedacht werden."
        ),
        fit_response=(
            "Zu adesso passt mein Profil gut, weil ich Gestaltung, Webentwicklung und "
            "nutzerorientierte digitale Konzeption zusammenbringe."
        ),
    ),
    "denkwerk": CompanyProfile(
        display_name="denkwerk",
        aliases=("denkwerk",),
        mention_response=(
            "denkwerk ist für mich interessant, weil ich mein Profil dort gut an der "
            "Schnittstelle von Gestaltung, digitalen Anwendungen und Nutzerführung "
            "einbringen könnte."
        ),
        why_response=(
            "denkwerk ist für mich interessant, weil dort kreatives Arbeiten, technische "
            "Umsetzung und digitales Produktdenken zusammenkommen."
        ),
        fit_response=(
            "Zu denkwerk passt mein Profil gut, weil ich eine Mischung aus "
            "Medieninformatik, Gestaltung, Webentwicklung und Chatbot-Konzeption "
            "mitbringe."
        ),
    ),
    "msg": CompanyProfile(
        display_name="msg",
        aliases=("msg",),
        mention_response=(
            "msg ist für mich besonders interessant, weil ich mein Profil dort gut in "
            "digitale Projekte mit praktischem Bezug einbringen könnte."
        ),
        why_response=(
            "msg ist für mich besonders interessant, weil dort technische Umsetzung, "
            "digitale Anwendungen und nutzerorientiertes Denken gut zusammenkommen."
        ),
        fit_response=(
            "Zu msg passt mein Profil gut, weil ich Medieninformatik, Gestaltung, "
            "Webentwicklung und Chatbot-Konzeption mitbringe."
        ),
    ),
    "machineseeker": CompanyProfile(
        display_name="Machineseeker",
        aliases=("machineseeker",),
        mention_response=(
            "Machineseeker ist für mich besonders interessant, weil ich mein Profil dort "
            "gut in digitale Anwendungen mit praktischem Bezug einbringen könnte."
        ),
        why_response=(
            "Machineseeker ist für mich spannend, weil dort Frontend, Features und digitale "
            "Plattformen mit praktischem Bezug zusammenkommen."
        ),
        fit_response=(
            "Zu Machineseeker passt mein Profil gut, weil ich Medieninformatik, Gestaltung, "
            "Webentwicklung und Chatbot-Konzeption mitbringe."
        ),
    ),
    "rewe digital": CompanyProfile(
        display_name="REWE digital",
        aliases=("rewe digital", "rewedigital"),
        mention_response=(
            "REWE digital ist für mich besonders interessant, weil ich mein Profil dort "
            "gut in digitale Anwendungen mit klarem Nutzerbezug einbringen könnte."
        ),
        why_response=(
            "REWE digital ist für mich spannend, weil dort UX/UI, digitale Produkte und "
            "real genutzte Anwendungen zusammenkommen."
        ),
        fit_response=(
            "Zu REWE digital passt mein Profil gut, weil ich Gestaltung, Nutzerführung, "
            "digitale Konzepte und praktische Umsetzung verbinde."
        ),
    ),
    "devk": CompanyProfile(
        display_name="DEVK",
        aliases=("devk",),
        mention_response=(
            "DEVK ist für mich interessant, weil die Stelle UX/UI, Nutzerperspektive "
            "und konkrete Anwendung verbindet."
        ),
        why_response=(
            "DEVK ist für mich interessant, weil dort Nutzerführung, verständliche "
            "digitale Anwendungen und die Verbindung von Funktionalität und Gestaltung "
            "zusammenkommen."
        ),
        fit_response=(
            "Zu DEVK passt mein Profil gut, weil ich Medieninformatik, Gestaltung, "
            "Webentwicklung und digitales Produktdenken mitbringe. Usability-Tests "
            "habe ich bereits mehrfach durchgeführt, mit Adobe XD arbeite ich seit "
            "Jahren vertraut und Entwicklungen in Design und User Experience verfolge "
            "ich aufmerksam."
        ),
    ),
    "taxy.io": CompanyProfile(
        display_name="taxy.io",
        aliases=("taxy.io", "taxy io", "taxyio"),
        mention_response=(
            "taxy.io ist für mich interessant, weil ich mein Profil dort gut in digitale "
            "Produkte mit praktischem Bezug einbringen könnte."
        ),
        why_response=(
            "taxy.io ist für mich interessant, weil dort technische Umsetzung, digitale "
            "Anwendungen und nutzerorientiertes Denken nah zusammenliegen."
        ),
        fit_response=(
            "Zu taxy.io passt mein Profil gut, weil ich Medieninformatik, Gestaltung, "
            "Webentwicklung und Chatbot-Konzeption mitbringe."
        ),
    ),
    "arag it": CompanyProfile(
        display_name="ARAG IT",
        aliases=("arag", "arag it", "arag-it", "aragit"),
        mention_response=(
            "ARAG IT ist für mich interessant, weil ich mein Profil dort gut in digitale "
            "Projekte mit praktischem Bezug einbringen könnte."
        ),
        why_response=(
            "ARAG IT ist für mich interessant, weil dort technische Umsetzung, digitale "
            "Anwendungen und nutzerorientiertes Denken gut zusammenkommen."
        ),
        fit_response=(
            "Zu ARAG IT passt mein Profil gut, weil ich Medieninformatik, Gestaltung, "
            "Webentwicklung und Chatbot-Konzeption mitbringe."
        ),
    ),
    "scala stage": CompanyProfile(
        display_name="SCALA stage systems & services",
        aliases=("scala", "scala stage", "scala stage systems", "scala stage systems services"),
        mention_response=(
            "SCALA stage systems & services ist für mich besonders interessant, weil die Stelle "
            "genau in die Richtung geht, die ich gerade suche: ein reales KI-Projekt mit Python, "
            "LLMs, RAG, Embeddings und technischem Wissen aus der Praxis. Dazu kommt dieses "
            "Theater- und Bühnentechnik-Umfeld, das sich für mich deutlich spannender anfühlt "
            "als eine klassische IT-Umgebung."
        ),
        why_response=(
            "An SCALA reizt mich vor allem die Kombination aus realem KI-Projekt und einem "
            "ungewöhnlich spannenden Umfeld. Der Aufgabenbereich passt sehr gut zu dem, was ich "
            "vertiefen möchte: Python, LLMs, RAG, Embeddings und der sinnvolle Umgang mit "
            "technischen Dokumentationen und Servicewissen."
        ),
        fit_response=(
            "Zu SCALA passt mein Profil, weil in meinem eigenen Projekt bereits Themen wie "
            "LLMs, Python, strukturierte Inhalte und dialogische Systeme sichtbar werden. Ich "
            "bringe noch nicht in jedem Bereich tiefe Praxiserfahrung mit, aber genau diese "
            "Richtung möchte ich konsequent vertiefen und arbeite mich gerne eigenständig in "
            "neue technische Zusammenhänge ein."
        ),
    ),
    "interaktiv": CompanyProfile(
        display_name="Interaktiv GmbH",
        aliases=("interaktiv", "interaktiv gmbh"),
        mention_response=(
            "Interaktiv passt für mich gut, weil die Stelle meine bisherigen Fähigkeiten mit "
            "einem neuen Feld verbindet, in das ich fachlich weiter hineinwachsen möchte. "
            "Ich bringe Gestaltung, Webentwicklung und erste Chatbot-Erfahrung mit und möchte "
            "genau darauf im KI-Bereich aufbauen."
        ),
        why_response=(
            "Mich reizt, dass es bei Interaktiv um praktische KI-Anwendungen geht: LLMs, "
            "Chatbots, RAG, API-Vergleiche und Prototyping. Das klingt nach einer Stelle, "
            "bei der ich nicht nur über KI lese, sondern praktisch mitarbeite und mein Wissen "
            "vertiefe."
        ),
        fit_response=(
            "Ich bringe eine Ausbildung zum Mediengestalter, ein fast abgeschlossenes "
            "Medieninformatik-Studium und Berufs- und Lebenserfahrung aus verschiedenen "
            "Bereichen mit. Dadurch verbinde ich Gestaltung, technisches Verständnis, "
            "praktische Umsetzung und Kommunikation."
        ),
    ),
}

WHY_TERMS = {"warum", "wieso", "weshalb"}
WHY_COMPANY_TERMS = {
    "bewerben",
    "bewerbung",
    "bewirbst",
    "bewerbe",
    "interessant",
    "spannend",
    "reizt",
    "reizvoll",
}
COMPANY_FIT_TERMS = {
    "passt",
    "passen",
    "profil",
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


def company_key_from_value(value: Optional[str]) -> Optional[str]:
    normalized = normalize_company_text(value or "")
    if not normalized:
        return None
    if normalized in COMPANY_PROFILES:
        return normalized
    return _find_company_key(normalized)


def _is_company_name_only(normalized: str, company_key: str) -> bool:
    profile = COMPANY_PROFILES[company_key]
    aliases = {normalize_company_text(alias) for alias in profile.aliases}
    return normalized in aliases


def _has_fit_company_intent(normalized: str, company_key: Optional[str]) -> bool:
    words = set(normalized.split())
    has_fit_term = any(term in words for term in COMPANY_FIT_TERMS)
    if company_key:
        return has_fit_term

    has_why_term = bool(words & WHY_TERMS) or any(term in words for term in WHY_COMPANY_TERMS)
    has_general_target = any(target in normalized for target in GENERAL_COMPANY_TARGETS)
    return has_general_target and has_fit_term and has_why_term


def _has_why_company_intent(normalized: str, company_key: Optional[str]) -> bool:
    words = set(normalized.split())
    has_why_term = bool(words & WHY_TERMS)
    has_why_context_term = any(term in words for term in WHY_COMPANY_TERMS)
    has_general_target = any(target in normalized for target in GENERAL_COMPANY_TARGETS)

    if company_key:
        return has_why_term or has_why_context_term

    return has_general_target and (has_why_term or has_why_context_term)


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
    company_key_hint: Optional[str] = None,
) -> Optional[CompanyContextResult]:
    normalized = normalize_company_text(message)
    if not normalized:
        return None

    message_company_key = current_company_from_message(message)
    company_key = message_company_key
    if company_key is None:
        company_key = company_key_from_value(company_key_hint)
    if company_key is None:
        company_key = current_company_from_conversation(history or [])
    has_fit_intent = _has_fit_company_intent(normalized, company_key)
    has_why_intent = _has_why_company_intent(normalized, company_key)

    if message_company_key:
        profile = COMPANY_PROFILES[company_key]
        if has_fit_intent and not _is_company_name_only(normalized, company_key):
            return CompanyContextResult(company_key, COMPANY_INTENT_FIT, profile.fit_response)
        if has_why_intent and not _is_company_name_only(normalized, company_key):
            return CompanyContextResult(company_key, COMPANY_INTENT_WHY, profile.why_response)
        return CompanyContextResult(company_key, COMPANY_INTENT_MENTION, profile.mention_response)

    if company_key and has_fit_intent:
        profile = COMPANY_PROFILES[company_key]
        return CompanyContextResult(company_key, COMPANY_INTENT_FIT, profile.fit_response)

    if company_key and has_why_intent:
        profile = COMPANY_PROFILES[company_key]
        return CompanyContextResult(company_key, COMPANY_INTENT_WHY, profile.why_response)

    if has_why_intent:
        return CompanyContextResult(None, COMPANY_INTENT_GENERAL_WHY, GENERAL_WHY_COMPANY_RESPONSE)

    return None


def build_company_context_response(
    message: str,
    history: Optional[Sequence[str]] = None,
    company_key_hint: Optional[str] = None,
) -> Optional[dict]:
    result = resolve_company_context(message, history=history, company_key_hint=company_key_hint)
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
