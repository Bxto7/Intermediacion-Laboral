Eres el agente python-pro. Lee el archivo CLAUDE.md en la raíz del repositorio antes de tocar cualquier archivo. Para todo el trabajo usa la herramienta Bash.

Implementa todo el código del Sprint 2 siguiendo exactamente las especificaciones del archivo sprint2_claude_code.md. Tu trabajo cubre los bloques 1, 2, 3 y 4:

BLOQUE 1 — Módulo de empleadores: crea app/models/job_offer.py, app/models/application.py, app/models/search_log.py, app/schemas/employer.py, app/schemas/job_offer.py, app/api/v1/employers.py, app/api/v1/jobs.py. Agrega los endpoints POST /workers/apply y GET /workers/applications en app/api/v1/workers.py. Agrega las tareas Celery stub notify_employer_new_application y notify_worker_hired en app/tasks/notifications.py. Registra los routers nuevos en app/main.py.

BLOQUE 2 — Motor NLP real: reemplaza los stubs del Sprint 1 con implementaciones reales en app/nlp/embeddings/generator.py (sentence-transformers paraphrase-multilingual-MiniLM-L12-v2, normalize_text, apply_local_dictionary), app/nlp/skill_extractor/first_job_extractor.py (40 términos coloquiales peruanos, extract_skills_from_wizard_answer, suggest_job_sectors), app/nlp/cv_parser/parser.py (parse_pdf, parse_docx, extract_cv_fields con umbrales de confianza), app/nlp/portfolio_nlp/trade_extractor.py (TRADE_SKILLS_MAP con 15+ skills para ELECTRICIDAD, GASFITERIA, CARPINTERIA, ALBANILERIA y PINTURA, extract_skills_from_job_description). Reemplaza los stubs de app/tasks/embeddings.py con generate_worker_embedding, generate_job_embedding, generate_portfolio_entry_embedding y regenerate_all_embeddings reales. Crea app/api/v1/nlp.py con los 5 endpoints del módulo NLP. Crea app/schemas/cv.py con ParsedCVResult.

BLOQUE 3 — Wizard PRIMER_EMPLEO: crea app/schemas/wizard.py, app/services/cv_builder/wizard_service.py con get_or_create_wizard, save_wizard_step y get_wizard_summary, y app/api/v1/wizard.py con GET /progress, POST /step y GET /summary.

BLOQUE 4 — Portfolio OFICIO: crea app/schemas/portfolio.py, app/api/v1/portfolio.py con POST /entries, GET /entries, GET /public/{username}, PATCH /entries/{entry_id}, DELETE /entries/{entry_id} y POST /entries/{entry_id}/photos.

Al terminar muéstrame la salida de:
ruff check app/
grep -r "print(" app/
