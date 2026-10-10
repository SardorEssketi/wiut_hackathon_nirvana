"""Deterministic Russian explanations shared by the UI and printable report.

No generated legal text: findings and their recorded source version are the facts.
"""
from collections import Counter
from .models import Finding, Report, Status

STATUS_LABELS = {
    Status.MATCH_FOUND: "Условие согласуется с проверяемым критерием",
    Status.POTENTIAL_CONFLICT: "Возможное несоответствие — нужна проверка",
    Status.NOT_FOUND: "Условие не найдено в проверенном тексте",
    Status.UNVERIFIABLE: "Недостаточно данных для проверки",
}
STATUS_ICONS = {Status.MATCH_FOUND: "✓", Status.POTENTIAL_CONFLICT: "!",
                Status.NOT_FOUND: "?", Status.UNVERIFIABLE: "—"}
REVIEW_LABELS = {"confirm": "Подтвердить находку", "dismiss": "Отклонить находку",
                 "further_review": "Передать на проверку"}
SECTION_LABELS = {"offer": "Текст оферты", "regulatory_appendix": "Нормативное приложение",
                  "uncertain": "Раздел не установлен"}
MODE_LABELS = {"hybrid": "Локальная AI-модель + поиск по словам", "semantic": "Локальная AI-модель",
               "lexical": "Поиск по словам (без AI-модели)"}
UNITS = {"UZS": "сум", "working_days": "рабочих дней", "days": "дней"}
SCOPES = {
    "OSAGO_SUM": "Явно указанная общая страховая сумма ОСАГО в сумах. Премия и отдельные лимиты не сравниваются.",
    "OSAGO_PAYMENT": "Срок выплаты страхового возмещения в рабочих днях после принятия решения страховщиком.",
    "OSAGO_DECISION_NOTICE": "Срок уведомления страхователя о решении после письменного или электронного обращения за возмещением.",
}
STANDARD_LIMITATIONS = [
    "Проверены только выбранные условия ОСАГО. Общая законность договора не оценивалась.",
    "Интерпретации ожидают проверки квалифицированным юристом: PENDING_LEGAL_REVIEW. Это не юридическое заключение.",
    "Отсутствие найденного текста не доказывает нарушение. Поиск, в том числе AI, может пропустить нужный пункт.",
    "OCR не поддерживается. Нечитаемые страницы, сложная верстка и поврежденный текст ограничивают выводы.",
    "Неизвестная дата или неподдерживаемая редакция нормы не позволяют сделать числовое сравнение.",
    "Отнесение текста к оферте или нормативному приложению эвристическое; его следует проверить по PDF.",
]


def counts(report: Report) -> dict[Status, int]:
    observed = Counter(f.status for f in report.findings)
    return {status: observed[status] for status in Status}


def summary(report: Report) -> str:
    c = counts(report)
    text = (f"Проверено условий: {len(report.findings)}. Возможных несоответствий: {c[Status.POTENTIAL_CONFLICT]}; "
            f"согласуются с критериями: {c[Status.MATCH_FOUND]}; не найдены: {c[Status.NOT_FOUND]}; "
            f"недостаточно данных: {c[Status.UNVERIFIABLE]}.")
    if c[Status.UNVERIFIABLE] == len(report.findings):
        return text + " Ни одно условие не удалось надежно проверить. Это не устанавливает нарушение закона."
    if c[Status.POTENTIAL_CONFLICT]:
        return text + " Специалисту следует проверить отмеченные положения и применимую редакцию нормы."
    return text + " Результат относится только к указанным проверкам и не подтверждает законность всего договора."


def format_value(value, unit=None) -> str:
    if value is None:
        return "Значение не установлено"
    number = f"{value:,.10g}".replace(",", " ")
    return f"{number} {UNITS.get(unit, unit or '')}".strip()


def observation(finding: Finding) -> str:
    values = list(dict.fromkeys((ev.extracted_value, ev.unit) for ev in finding.evidence
                               if ev.extracted_value is not None))
    if values:
        text = "В тексте извлечено: " + "; ".join(format_value(*v) for v in values) + "."
        if finding.status == Status.UNVERIFIABLE:
            text += " Эти значения недостаточны для надежного сравнения; см. причину."
        return text
    if not finding.evidence:
        return "Подходящее доказательство не найдено. Числовое значение не установлено."
    return "Найден связанный текст, но сопоставимое числовое условие не установлено."


def expected(finding: Finding) -> str:
    if finding.expected_value is None:
        return "Применимая версия нормы не установлена; ориентир не выбран."
    unit = "UZS" if finding.rule_id == "OSAGO_SUM" else (
        "working_days" if finding.rule_id == "OSAGO_PAYMENT" else "days")
    operator = "Ориентир общей суммы: " if unit == "UZS" else "Предельный срок для этой проверки: "
    return operator + format_value(finding.expected_value, unit) + "."


def next_step(finding: Finding) -> str:
    if "applicable_date_unknown" in finding.uncertainty:
        return "Установите дату применимости договора по первичным документам и повторите проверку."
    if "unsupported_applicability_date" in finding.uncertainty:
        return "Проверьте даты и обратитесь к специалисту за редакцией нормы для этой даты."
    if "appendix_only" in finding.uncertainty:
        return "Проверьте, как правила приложения включены в договор. Текст закона не подтверждает обязательство автора оферты."
    if "incorporation_by_reference" in finding.uncertainty:
        return "Откройте указанные в договоре правила и передайте вопрос об их применимости на правовую проверку."
    return {
        Status.MATCH_FOUND: "Сверьте цитату, дату и контекст в оригинале. Совпадение этого условия не подтверждает весь договор.",
        Status.POTENTIAL_CONFLICT: "Сверьте значение, событие и дату в PDF; передайте положение специалисту для правовой проверки.",
        Status.NOT_FOUND: "Проверьте оригинал и связанные документы вручную. Не считайте отсутствие находки нарушением.",
        Status.UNVERIFIABLE: "Проверьте оригинальный текст, единицы, событие и конкурирующие условия; при необходимости запросите читаемый PDF.",
    }[finding.status]


def explanation(finding: Finding) -> str:
    if finding.status == Status.POTENTIAL_CONFLICT and finding.expected_value is not None:
        comparable = [ev for ev in finding.evidence if ev.extracted_value is not None]
        if comparable:
            ev = comparable[0]
            return (f"В документе указано {format_value(ev.extracted_value, ev.unit)}, а ориентир выбранной редакции — "
                    f"{format_value(finding.expected_value, ev.unit)}. Числовое расхождение требует проверки специалистом.")
    return finding.reason


def period(finding: Finding) -> str:
    if finding.effective_from is None:
        return "Применимая редакция не установлена"
    return f"С {finding.effective_from} по {finding.effective_to or 'конец подтвержденного диапазона каталога'}"
