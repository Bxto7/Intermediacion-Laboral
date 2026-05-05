# RF: RF066-RF070
import io
import re

import structlog

from app.schemas.cv import ParsedCVResult

logger = structlog.get_logger()

_nlp = None

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+51\s?)?9\d{8}")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
EDUCATION_KEYWORDS = {"universidad", "instituto", "colegio", "bachiller", "licenciado", "tecnico", "maestria", "doctorado"}
SKILLS_SECTION_RE = re.compile(r"(habilidades|competencias|skills|manejo de)[:\s]+(.*?)(?:\n\n|\Z)", re.IGNORECASE | re.DOTALL)


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("es_core_news_md")
        except Exception:
            _nlp = None
    return _nlp


def parse_pdf(file_content: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if len(text.strip()) < 100:
            logger.warning("pdf_no_text_extracted", length=len(text.strip()))
            return ""
        return text
    except Exception as exc:
        logger.warning("pdf_parse_error", error=str(exc))
        return ""


def parse_docx(file_content: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:
        logger.warning("docx_parse_error", error=str(exc))
        return ""


def extract_cv_fields(raw_text: str) -> ParsedCVResult:
    result = ParsedCVResult(raw_text_length=len(raw_text))
    warnings: list[str] = []
    lines = raw_text.split("\n")
    first_lines = " ".join(lines[:10])

    nlp = _get_nlp()

    full_name: str | None = None
    full_name_confidence = 0.0
    if nlp is not None:
        doc = nlp(first_lines[:500])
        persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        if len(persons) == 1:
            full_name = persons[0]
            full_name_confidence = 0.85
        elif len(persons) > 1:
            full_name = persons[0]
            full_name_confidence = 0.5
    else:
        name_re = re.search(r"^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})", raw_text.strip(), re.MULTILINE)
        if name_re:
            full_name = name_re.group(1)
            full_name_confidence = 0.6

    if full_name_confidence < 0.75:
        full_name = None
        warnings.append("No se pudo extraer nombre completo con suficiente confianza (< 0.75)")

    result.full_name = full_name
    result.full_name_confidence = full_name_confidence

    emails = EMAIL_RE.findall(raw_text)
    if len(emails) == 1:
        result.email = emails[0]
        result.email_confidence = 0.99
    elif len(emails) > 1:
        result.email = emails[0]
        result.email_confidence = 0.80
    else:
        warnings.append("No se encontro email en el CV")

    phones = PHONE_RE.findall(raw_text)
    if phones:
        result.phone = phones[0]
        result.phone_confidence = 0.95
    else:
        warnings.append("No se encontro telefono en formato peruano")

    education_entries: list[dict] = []
    education_confidence = 0.0
    text_lower = raw_text.lower()
    for kw in EDUCATION_KEYWORDS:
        idx = text_lower.find(kw)
        if idx != -1:
            context = raw_text[max(0, idx - 10):idx + 150]
            inst = ""
            if nlp is not None:
                doc = nlp(context)
                orgs = [e.text for e in doc.ents if e.label_ == "ORG"]
                inst = orgs[0] if orgs else ""
            years = YEAR_RE.findall(context)
            education_entries.append({"keyword": kw, "institution": inst, "years": years, "context": context.strip()})
            education_confidence = 0.80

    result.education = education_entries
    result.education_confidence = education_confidence
    if education_confidence < 0.75:
        result.education = []
        warnings.append("Educacion extraida con baja confianza (< 0.75)")

    work_entries: list[dict] = []
    work_confidence = 0.0
    year_matches = list(YEAR_RE.finditer(raw_text))
    for m in year_matches:
        context = raw_text[max(0, m.start() - 50):m.end() + 200]
        org = ""
        if nlp is not None:
            doc = nlp(context)
            orgs = [e.text for e in doc.ents if e.label_ == "ORG"]
            org = orgs[0] if orgs else ""
        if org:
            work_entries.append({"year": m.group(), "company": org, "context": context.strip()[:200]})
            work_confidence = 0.70

    result.work_experiences = work_entries
    result.work_experiences_confidence = work_confidence
    if work_confidence < 0.75:
        result.work_experiences = []
        warnings.append("Experiencias laborales extraidas con baja confianza (< 0.75)")

    skills: list[str] = []
    skills_confidence = 0.0
    m = SKILLS_SECTION_RE.search(raw_text)
    if m:
        raw_skills = m.group(2)
        skills = [s.strip() for s in re.split(r"[,;\n•\-]", raw_skills) if s.strip() and len(s.strip()) > 1]
        skills = skills[:20]
        if skills:
            skills_confidence = 0.75

    result.skills = skills
    result.skills_confidence = skills_confidence
    if skills_confidence < 0.75:
        result.skills = []
        warnings.append("Habilidades extraidas con baja confianza (< 0.75)")

    result.parse_warnings = warnings
    return result
