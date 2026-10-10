"""Deterministic multilingual explanations shared by the UI and printable report.

No generated legal text: findings and their recorded source version are the facts.
"""
from collections import Counter
from .models import Finding, Report, Status
from .i18n import tr, recorded_text

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


def labels(mapping, language="ru"):
    return {key: tr(value, language) for key, value in mapping.items()}


RULE_NAMES = {"OSAGO_SUM": "Страховая сумма ОСАГО",
              "OSAGO_PAYMENT": "Срок выплаты после решения страховщика",
              "OSAGO_DECISION_NOTICE": "Срок уведомления о решении"}


def rule_name(rule, language="ru"):
    rule_id = rule.rule_id if isinstance(rule, Finding) else rule.id
    if rule_id in RULE_NAMES:
        return tr(RULE_NAMES[rule_id], language)
    return getattr(rule, "rule_name", getattr(rule, "name", ""))


def summary(report: Report, language="ru") -> str:
    c = counts(report)
    text = tr("Проверено условий: {total}. Возможных несоответствий: {conflicts}; согласуются с критериями: {matches}; не найдены: {missing}; недостаточно данных: {unverifiable}.", language,
              total=len(report.findings), conflicts=c[Status.POTENTIAL_CONFLICT], matches=c[Status.MATCH_FOUND],
              missing=c[Status.NOT_FOUND], unverifiable=c[Status.UNVERIFIABLE])
    if c[Status.UNVERIFIABLE] == len(report.findings):
        return text + " " + tr("Ни одно условие не удалось надежно проверить. Это не устанавливает нарушение закона.", language)
    if c[Status.POTENTIAL_CONFLICT]:
        return text + " " + tr("Специалисту следует проверить отмеченные положения и применимую редакцию нормы.", language)
    return text + " " + tr("Результат относится только к указанным проверкам и не подтверждает законность всего договора.", language)


def format_value(value, unit=None, language="ru") -> str:
    if value is None:
        return tr("Значение не установлено", language)
    number = f"{value:,.10g}".replace(",", " ")
    return f"{number} {labels(UNITS, language).get(unit, unit or '')}".strip()


def observation(finding: Finding, language="ru") -> str:
    values = list(dict.fromkeys((ev.extracted_value, ev.unit) for ev in finding.evidence
                               if ev.extracted_value is not None))
    if values:
        text = tr("В тексте извлечено: ", language) + "; ".join(format_value(*v, language=language) for v in values) + "."
        if finding.status == Status.UNVERIFIABLE:
            text += " " + tr("Эти значения недостаточны для надежного сравнения; см. причину.", language)
        return text
    if not finding.evidence:
        return tr("Подходящее доказательство не найдено. Числовое значение не установлено.", language)
    return tr("Найден связанный текст, но сопоставимое числовое условие не установлено.", language)


def expected(finding: Finding, language="ru") -> str:
    if finding.expected_value is None:
        return tr("Применимая версия нормы не установлена; ориентир не выбран.", language)
    unit = "UZS" if finding.rule_id == "OSAGO_SUM" else (
        "working_days" if finding.rule_id == "OSAGO_PAYMENT" else "days")
    operator = "Ориентир общей суммы: " if unit == "UZS" else "Предельный срок для этой проверки: "
    return tr(operator, language) + format_value(finding.expected_value, unit, language) + "."


def next_step(finding: Finding, language="ru") -> str:
    if "applicable_date_unknown" in finding.uncertainty:
        return tr("Установите дату применимости договора по первичным документам и повторите проверку.", language)
    if "unsupported_applicability_date" in finding.uncertainty:
        return tr("Проверьте даты и обратитесь к специалисту за редакцией нормы для этой даты.", language)
    if "appendix_only" in finding.uncertainty:
        return tr("Проверьте, как правила приложения включены в договор. Текст закона не подтверждает обязательство автора оферты.", language)
    if "incorporation_by_reference" in finding.uncertainty:
        return tr("Откройте указанные в договоре правила и передайте вопрос об их применимости на правовую проверку.", language)
    return tr({
        Status.MATCH_FOUND: "Сверьте цитату, дату и контекст в оригинале. Совпадение этого условия не подтверждает весь договор.",
        Status.POTENTIAL_CONFLICT: "Сверьте значение, событие и дату в PDF; передайте положение специалисту для правовой проверки.",
        Status.NOT_FOUND: "Проверьте оригинал и связанные документы вручную. Не считайте отсутствие находки нарушением.",
        Status.UNVERIFIABLE: "Проверьте оригинальный текст, единицы, событие и конкурирующие условия; при необходимости запросите читаемый PDF.",
    }[finding.status], language)


def explanation(finding: Finding, language="ru") -> str:
    if finding.status == Status.POTENTIAL_CONFLICT and finding.expected_value is not None:
        comparable = [ev for ev in finding.evidence if ev.extracted_value is not None]
        if comparable:
            ev = comparable[0]
            return tr("В документе указано {actual}, а ориентир выбранной редакции — {reference}. Числовое расхождение требует проверки специалистом.", language,
                      actual=format_value(ev.extracted_value, ev.unit, language), reference=format_value(finding.expected_value, ev.unit, language))
    return recorded_text(finding.reason, language)


def period(finding: Finding, language="ru") -> str:
    if finding.effective_from is None:
        return tr("Применимая редакция не установлена", language)
    return tr("С {start} по {end}", language, start=finding.effective_from,
              end=finding.effective_to or tr("конец подтвержденного диапазона каталога", language))
