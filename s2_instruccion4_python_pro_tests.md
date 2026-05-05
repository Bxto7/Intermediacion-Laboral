Eres el agente python-pro. Lee el archivo CLAUDE.md en la raíz del repositorio antes de tocar cualquier archivo. Para todo el trabajo usa la herramienta Bash.

Escribe todos los tests del Sprint 2 y ejecuta la suite completa. Sigue exactamente las especificaciones del archivo sprint2_claude_code.md, Bloque 6.

Crea los siguientes archivos de test con todos los casos especificados en el sprint2_claude_code.md:

tests/unit/test_nlp_first_job.py — 11 tests: extract_skills_puntual, extract_skills_trabajador, extract_skills_informal_carpinteria, suggest_sectors_cocina, suggest_sectors_construccion, normalize_text_removes_stopwords, normalize_text_fixes_encoding, apply_local_dictionary_gasfitero, apply_local_dictionary_case_insensitive, apply_local_dictionary_fierrero, build_first_job_profile_text_format.

tests/unit/test_nlp_cv_parser.py — 6 tests: extract_email_confidence_099, extract_phone_peruvian_format, extract_two_emails_low_confidence, low_confidence_field_returns_none, parse_docx_returns_string, empty_text_produces_warnings.

tests/unit/test_nlp_trade_portfolio.py — 7 tests: extract_skills_electricidad_cableado, extract_skills_electricidad_tablero, extract_skills_gasfiteria_cañeria, estimated_level_basico, estimated_level_avanzado, build_trade_profile_text_contains_category, confidence_between_0_and_1.

tests/unit/test_embeddings.py — 5 tests: generate_embedding_returns_384_dims, normalized_embedding_unit_length, generate_embeddings_batch_two_texts, local_dict_cache_not_reloaded, apply_local_dict_replaces_term.

Agrega en tests/unit/test_security.py los 4 tests nuevos del sprint: test_reset_password_invalidates_all_sessions, test_get_client_ip_from_forwarded_for, test_rate_limit_blocks_after_threshold, test_forgot_password_schema_validates_email.

tests/integration/test_api_employers.py — 12 tests: create_employer_profile_returns_201, create_duplicate_employer_returns_409, ruc_never_in_response, contact_name_never_in_response, create_job_offer_returns_201_and_queues_task, deactivate_job_offer_sets_inactive, application_status_flow_valid, application_status_flow_invalid, apply_requires_min_completeness, apply_duplicate_returns_409, jobs_feed_is_public, jobs_feed_filters_by_district.

tests/integration/test_api_nlp.py — 7 tests: extract_skills_wizard_primer_empleo_only, extract_skills_wizard_returns_skills, parse_cv_experiencia_only, parse_cv_invalid_mime_type, parse_cv_file_too_large, extract_portfolio_skills_oficio_only, extract_portfolio_skills_returns_result.

tests/integration/test_api_portfolio.py — 11 tests: create_entry_returns_201_with_skills, create_requires_oficio_type, create_requires_trade_category, get_entries_returns_list, public_portfolio_no_auth, public_hides_sensitive_data, non_oficio_worker_public_404, update_entry_recalculates_rating, delete_returns_204, photo_upload_invalid_mime, photo_upload_too_large.

tests/integration/test_api_wizard.py — 8 tests: progress_creates_if_not_exists, step_1_saves_data, step_3_extracts_skills, cannot_skip_steps, step_6_updates_completeness, summary_before_step_6_returns_400, summary_returns_skills, requires_primer_empleo.

Si algún test falla, corrígelo antes de terminar. Al terminar muéstrame la salida de:
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v
ruff check .
