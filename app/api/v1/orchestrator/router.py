from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Union, Optional
from app.pipeline.orchestrator_v7 import orchestrate
from app.pipeline.orchestrator_v8 import orchestrate_v8
from app.pipeline.exporter.pdf_exporter import PDFExporter
from app.pipeline.exporter.excel_exporter import excel_exporter
from app.db.session import get_db
from app.api.deps.auth import get_current_active_user, can_access_session, can_access_session
from app.models.user import User
from app.models.session import OrchestratorSession
from app.services.session_service import SessionService
from app.services.document_service import document_service
from app.services.rag_service import rag_service
from app.services.advanced_rag_service import advanced_rag_service
from app.services.cache_service import cache_service
from app.core.logging_config import get_logger
from app.schemas.llm_schema import LLMConfiguration, MultiLLMStrategy, LLMProvider, ModelConfig
import asyncio
import time
import io

router = APIRouter()
logger = get_logger(__name__)
pdf_exporter = PDFExporter()


@router.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get cache statistics

    Shows cache performance metrics including hit rate
    """
    stats = cache_service.get_stats()
    return stats


@router.post("/run")
async def run_orch(
    payload: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)  # Still needed for RAG and auth
):
    """
    Run orchestrator with authentication and session tracking

    Generates functional, negative, and boundary test cases from requirements.

    ## Simple LLM Mode (Recommended)

    ### 1. Local LLM Only (Ollama):
    ```json
    {
        "requirement": "User login feature",
        "llm_config": {
            "mode": "local_only"
        }
    }
    ```

    ### 2. GLM API Only:
    ```json
    {
        "requirement": "User login feature",
        "llm_config": {
            "mode": "glm_only"
        }
    }
    ```

    ### 3. Combined (Both Local + GLM):
    ```json
    {
        "requirement": "User login feature",
        "llm_config": {
            "mode": "combined"
        }
    }
    ```

    ### Custom Model Selection (Simple Mode):
    ```json
    {
        "requirement": "User login feature",
        "llm_config": {
            "mode": "combined",
            "local_model": "mistral:7b",
            "glm_model": "glm-4-flash",
            "local_weight": 0.7,
            "glm_weight": 0.3
        }
    }
    ```

    ## Advanced Configuration

    ### Full Control with Strategy:
    ```json
    {
        "requirement": "User login feature",
        "llm_config": {
            "strategy": "ensemble",
            "primary": {"provider": "ollama", "model": "llama3.1:8b", "weight": 0.6},
            "secondary": [
                {"provider": "glm", "model": "glm-4.5-flash", "weight": 0.4}
            ]
        }
    }
    ```

    ## Supported Providers:
    - `ollama`: Local Ollama models (llama3.1, mistral, phi, etc.)
    - `glm`: GLM API (glm-4.5-flash, glm-4-flash, etc.)
    """
    start_time = time.time()

    # Parse LLM configuration
    model_config = _parse_llm_config(payload)

    logger.info(
        "orchestrator_request",
        user_id=current_user.id,
        username=current_user.username,
        model_config=model_config
    )

    try:
        requirement = payload["requirement"]
        use_rag = payload.get("use_rag", True)  # Enable RAG by default

        # Advanced RAG options
        use_advanced_rag = payload.get("use_advanced_rag", True)  # Use advanced RAG by default
        use_query_expansion = payload.get("use_query_expansion", True)
        use_reranking = payload.get("use_reranking", True)
        rag_top_k = payload.get("rag_top_k", 5)

        # Step 1: Retrieve context using RAG (if enabled)
        rag_context = None
        citation_metadata = None

        if use_rag:
            if use_advanced_rag:
                rag_start = time.time()
                logger.info(
                    "Retrieving context with advanced RAG",
                    user_id=current_user.id,
                    query_expansion=use_query_expansion,
                    reranking=use_reranking
                )

                # Use advanced RAG with all features
                docs, citation_metadata = await advanced_rag_service.retrieve_with_citations(
                    requirement=requirement,
                    user_id=current_user.id,
                    db=db,
                    top_k=rag_top_k,
                    use_query_expansion=use_query_expansion,
                    use_reranking=use_reranking
                )
                rag_time = int((time.time() - rag_start) * 1000)
                logger.info(f"Advanced RAG completed in {rag_time}ms", rag_time_ms=rag_time)

                # Convert to format expected by orchestrator
                rag_context = {
                    "similar_documents": docs,
                    "similar_test_cases": [],  # Already included in docs
                    "similar_requirements": [],  # Already included in docs
                    "best_practices": []
                }

                logger.info(
                    "Advanced RAG context retrieved",
                    total_docs=len(docs),
                    queries_used=len(citation_metadata.get("query_variations", [])),
                    reranking=use_reranking
                )
            else:
                # Use basic RAG (backward compatibility)
                logger.info("Retrieving RAG context (basic)", user_id=current_user.id)
                rag_context = await rag_service.retrieve_context_for_generation(
                    requirement=requirement,
                    user_id=current_user.id,
                    db=db,
                    top_k=rag_top_k
                )
                logger.info(
                    "Basic RAG context retrieved",
                    documents=len(rag_context.get("similar_documents", [])),
                    test_cases=len(rag_context.get("similar_test_cases", [])),
                    requirements=len(rag_context.get("similar_requirements", []))
                )

        # Step 2: Check cache before running orchestrator
        # Create cache key from model config
        cache_model_key = _model_config_to_cache_key(model_config)

        # ---- V8 document-driven path ----
        # Support multiple documents: frontend may send `document_ids: [int, ...]`
        # (preferred) or a single legacy `document_id: int`. We fetch + concat
        # all selected documents' full_text so the LLM gets a rich, mixed context
        # (e.g. PRD + user stories + Figma flow). Fall back to v7 if none provided.
        document_ids_raw = payload.get("document_ids")
        if document_ids_raw is None:
            single = payload.get("document_id")
            document_ids_raw = [single] if single is not None else []

        # Normalize to a deduped list of ints
        document_ids = []
        for did in document_ids_raw:
            try:
                document_ids.append(int(did))
            except (TypeError, ValueError):
                pass
        document_ids = list(dict.fromkeys(document_ids))  # dedupe, preserve order

        # Fetch + concat every requested document
        document_text_parts = []
        resolved_doc_ids = []
        for did in document_ids:
            try:
                document = await document_service.get_document(
                    document_id=did,
                    user_id=current_user.id,
                    db=db,
                )
                if document.full_text:
                    document_text_parts.append(
                        f"=== DOCUMENT: {document.title or document.filename} (id={did}) ===\n"
                        f"{document.full_text}"
                    )
                    resolved_doc_ids.append(did)
            except (ValueError, Exception) as e:
                logger.warning(
                    "document_id not found; skipping",
                    document_id=did, error=str(e),
                )

        document_text = "\n\n\n".join(document_text_parts) if document_text_parts else None
        document_id_key = tuple(resolved_doc_ids)  # for cache uniqueness

        if document_text:
            logger.info(
                "V8 document-driven generation",
                user_id=current_user.id,
                document_ids=resolved_doc_ids,
                document_count=len(resolved_doc_ids),
                document_chars=len(document_text),
            )

        cache_params = {
            "requirement": requirement,
            "model": cache_model_key,
            "generate_boundary": payload.get("generate_boundary", True),
            "include_risk": payload.get("include_risk_assessment", True),
            "use_rag": use_rag,
            "use_advanced_rag": use_advanced_rag,
            "use_query_expansion": use_query_expansion,
            "use_reranking": use_reranking,
            "document_ids": document_id_key,  # include so different doc sets don't collide
            "targets": payload.get("targets"),  # volume knob changes must not hit stale cache
            "use_history": payload.get("use_history", True),  # exemplar learning toggle
        }

        cached_result = cache_service.get("orchestrator", cache_params)
        from_cache = cached_result is not None

        if cached_result:
            logger.info(
                "Cache hit - returning cached result",
                user_id=current_user.id,
                requirement_preview=requirement[:50]
            )
            result = cached_result
            execution_time_ms = 0  # Instant from cache
        else:
            # Cache miss - run orchestrator
            orchestrate_start = time.time()
            logger.info("Cache miss - generating test cases", user_id=current_user.id)

            if document_text:
                # V8: powerful document-driven generation (single or multi-doc)
                # Optional volume knob: {"targets": {"functional": 60, "negative": 60, "boundary": 50}}
                raw_targets = payload.get("targets")
                explicit_targets = None
                if isinstance(raw_targets, dict):
                    explicit_targets = {
                        k: int(v)
                        for k, v in raw_targets.items()
                        if k in ("functional", "negative", "boundary") and str(v).isdigit()
                    } or None

                result = await orchestrate_v8(
                    document_text=document_text,
                    model=model_config,
                    requirement=requirement,
                    generate_boundary=payload.get("generate_boundary", True),
                    include_risk=payload.get("include_risk_assessment", True),
                    targets=explicit_targets,
                    use_history=payload.get("use_history", True),
                    user_id=current_user.id,
                )
            else:
                # V7: legacy free-text + RAG generation
                result = await orchestrate(
                    requirement=requirement,
                    model=model_config,
                    generate_boundary=payload.get("generate_boundary", True),
                    include_risk=payload.get("include_risk_assessment", True),
                    rag_context=rag_context  # Pass RAG context to orchestrator
                )

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            orchestrate_time = int((time.time() - orchestrate_start) * 1000)
            logger.info(f"Orchestration completed in {orchestrate_time}ms", orchestrate_time_ms=orchestrate_time)

            # Store in cache for future requests
            cache_service.set("orchestrator", cache_params, result)

        # Save session to database with fresh connection
        import uuid
        from app.core.config import settings
        from app.db.session import AsyncSessionLocal

        session_id = str(uuid.uuid4())  # Always generate a session ID

        if settings.ENABLE_SESSION_PERSISTENCE:
            # Use a fresh database connection to avoid timeout issues
            try:
                async with AsyncSessionLocal() as fresh_db:
                    session_service = SessionService(fresh_db)
                    session = await session_service.create_session(
                        user_id=current_user.id,
                        requirement_text=payload["requirement"],
                        model_used=_model_config_to_string(model_config),
                        generate_boundary=payload.get("generate_boundary", True),
                        include_risk=payload.get("include_risk_assessment", True),
                        result=result,
                        execution_time_ms=execution_time_ms
                    )
                    await fresh_db.commit()  # Commit the transaction
                    session_id = session.session_id
                    logger.info("Session saved to database", session_id=session_id)
            except Exception as db_error:
                logger.warning(
                    "Failed to save session to database",
                    error=str(db_error),
                    user_id=current_user.id
                )
        else:
            logger.debug("Session persistence disabled, using temporary session ID")

        # RAG exemplar learning: index the generated TCs into Qdrant (background —
        # embedding/upserting 200 TCs must not delay the API response)
        if settings.ENABLE_SESSION_PERSISTENCE and not from_cache:
            async def _index_generated_tcs():
                try:
                    from app.services.exemplar_service import exemplar_service
                    count = await exemplar_service.store_generated_test_cases(
                        session_id=session_id,
                        user_id=current_user.id,
                        requirement=payload["requirement"],
                        tcs_by_category={
                            "functional": result.get("functional", []),
                            "negative": result.get("negative", []),
                            "boundary": result.get("boundary", []),
                        },
                    )
                    if count:
                        logger.info("Exemplars indexed", session_id=session_id, count=count)
                except Exception as e:
                    logger.warning("Exemplar indexing failed", session_id=session_id, error=str(e))

            asyncio.create_task(_index_generated_tcs())

        # Add session_id to response
        result["session_id"] = session_id

        # Add citation metadata if advanced RAG was used
        if use_advanced_rag and citation_metadata:
            result["citations"] = citation_metadata
            result["rag_config"] = {
                "advanced_rag": True,
                "query_expansion": use_query_expansion,
                "reranking": use_reranking,
                "top_k": rag_top_k,
                "total_docs_retrieved": citation_metadata.get("total_results", 0)
            }
        elif use_rag:
            result["rag_config"] = {
                "advanced_rag": False,
                "basic_rag": True
            }

        # Store generated test cases in Qdrant for future RAG retrieval
        if use_rag and rag_context is not None:
            all_test_cases = []

            # Combine all test case types
            for tc in result.get("functional", []):
                tc["tc_type"] = "functional"
                all_test_cases.append(tc)

            for tc in result.get("negative", []):
                tc["tc_type"] = "negative"
                all_test_cases.append(tc)

            for tc in result.get("boundary", []):
                tc["tc_type"] = "boundary"
                all_test_cases.append(tc)

            # Store in vector database
            await rag_service.store_generated_test_cases(
                session_id=str(session_id),
                test_cases=all_test_cases,
                requirement=requirement,
                user_id=current_user.id
            )

            logger.info(
                "Stored test cases in vector DB",
                session_id=session_id,
                count=len(all_test_cases)
            )

        logger.info(
            "orchestrator_success",
            user_id=current_user.id,
            session_id=session_id,
            execution_time_ms=execution_time_ms,
            functional_count=len(result.get("functional", [])),
            negative_count=len(result.get("negative", [])),
            boundary_count=len(result.get("boundary", [])),
            has_summary=bool(result.get("summary")),
            response_size_bytes=len(str(result))
        )

        return result

    except Exception as e:
        logger.error(
            "orchestrator_error",
            user_id=current_user.id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def generate_pdf(
    payload: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF report from orchestrator results.

    Two modes:
    1. From session_id: {"session_id": "uuid"}
    2. From fresh data: {"requirement": "...", "functional": [...], ...}
    """
    from app.core.config import settings

    logger.info("pdf_generation_request", user_id=current_user.id)

    try:
        # Mode 1: Load from session_id
        if "session_id" in payload:
            session_id = payload["session_id"]

            # Fetch session from database
            result = await db.execute(
                select(OrchestratorSession).where(
                    OrchestratorSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            # RBAC: owner, squad-mates (qa_lead), kabag/admin — mirrors history detail
            if not session or not await can_access_session(session.user_id, current_user, db):
                raise HTTPException(status_code=404, detail="Session not found")

            # Build result dict from session
            result_data = {
                "functional": [],
                "negative": [],
                "boundary": [],
                "summary": session.summary,
                "risk": session.risk_assessment,
                "coverage_matrix": session.coverage_matrix,
                "metadata": session.session_metadata
            }

            # Fetch test cases
            from app.models.test_case import TestCaseRecord
            tc_result = await db.execute(
                select(TestCaseRecord).where(TestCaseRecord.session_id == session.id)
            )
            test_cases = tc_result.scalars().all()

            for tc in test_cases:
                tc_data = {
                    "tc_id": tc.tc_id,
                    "title": tc.title,
                    "preconditions": tc.preconditions,
                    "steps": tc.steps,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority,
                    "module": tc.module,
                    "test_data": tc.test_data,
                    "postconditions": tc.postconditions,
                }

                if tc.tc_type.value == "functional":
                    result_data["functional"].append(tc_data)
                elif tc.tc_type.value == "negative":
                    result_data["negative"].append(tc_data)
                elif tc.tc_type.value == "boundary":
                    result_data["boundary"].append(tc_data)

            requirement = session.requirement_text
            model = session.model_used

        # Mode 2: Use fresh data from payload
        else:
            if "requirement" not in payload:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'session_id' or 'requirement' must be provided"
                )

            result_data = {
                "functional": payload.get("functional", []),
                "negative": payload.get("negative", []),
                "boundary": payload.get("boundary", []),
                "summary": payload.get("summary", {}),
                "risk": payload.get("risk", {}),
                "coverage_matrix": payload.get("coverage_matrix", {}),
                "metadata": payload.get("metadata", {})
            }
            requirement = payload["requirement"]
            model = payload.get("model", settings.DEFAULT_LLM_MODEL)

        # Generate PDF
        pdf_bytes = pdf_exporter.generate_pdf(
            result=result_data,
            requirement=requirement,
            model=model
        )

        # Create filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_cases_{timestamp}.pdf"

        logger.info(
            "pdf_generated_successfully",
            user_id=current_user.id,
            filename=filename,
            size_bytes=len(pdf_bytes)
        )

        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "pdf_generation_error",
            user_id=current_user.id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/excel")
async def generate_excel(
    payload: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate Excel (.xlsx) report from orchestrator results.

    Two modes (mirrors /pdf):
    1. From session_id: {"session_id": "uuid"}
    2. From fresh data: {"requirement": "...", "functional": [...], ...}
    """
    from app.core.config import settings
    from datetime import datetime

    logger.info("excel_generation_request", user_id=current_user.id)

    try:
        session_obj = None
        # Mode 1: Load from session_id
        if "session_id" in payload:
            session_id = payload["session_id"]

            result = await db.execute(
                select(OrchestratorSession).where(
                    OrchestratorSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()
            session_obj = session
            # RBAC: owner, squad-mates (qa_lead), kabag/admin — mirrors history detail
            if not session or not await can_access_session(session.user_id, current_user, db):
                raise HTTPException(status_code=404, detail="Session not found")

            result_data = {
                "functional": [],
                "negative": [],
                "boundary": [],
                "summary": session.summary,
                "risk": session.risk_assessment,
                "coverage_matrix": session.coverage_matrix,
                "metadata": session.session_metadata,
            }

            from app.models.test_case import TestCaseRecord
            tc_result = await db.execute(
                select(TestCaseRecord).where(TestCaseRecord.session_id == session.id)
            )
            for tc in tc_result.scalars().all():
                tc_data = {
                    "tc_id": tc.tc_id,
                    "title": tc.title,
                    "preconditions": tc.preconditions,
                    "steps": tc.steps,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority,
                    "module": tc.module,
                    "test_data": tc.test_data,
                    "postconditions": tc.postconditions,
                }
                if tc.tc_type.value == "functional":
                    result_data["functional"].append(tc_data)
                elif tc.tc_type.value == "negative":
                    result_data["negative"].append(tc_data)
                elif tc.tc_type.value == "boundary":
                    result_data["boundary"].append(tc_data)

            requirement = session.requirement_text
            model = session.model_used

        # Mode 2: Use fresh data from payload
        else:
            if "requirement" not in payload:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'session_id' or 'requirement' must be provided"
                )
            result_data = {
                "functional": payload.get("functional", []),
                "negative": payload.get("negative", []),
                "boundary": payload.get("boundary", []),
                "summary": payload.get("summary", {}),
                "risk": payload.get("risk", {}),
                "coverage_matrix": payload.get("coverage_matrix", {}),
                "metadata": payload.get("metadata", {}),
            }
            requirement = payload["requirement"]
            model = payload.get("model", settings.DEFAULT_LLM_MODEL)

        # Generate .xlsx
        xlsx_bytes = excel_exporter.generate_excel(
            result=result_data,
            requirement=requirement,
            model=model,
        )

        # Descriptive filename: TC_<requirement-slug>_<timestamp>_<count>TC.xlsx
        import re as _re
        tc_count = (
            len(result_data["functional"])
            + len(result_data["negative"])
            + len(result_data["boundary"])
        )
        slug = _re.sub(
            r"[^A-Za-z0-9]+", "-", (requirement or "Test Cases").strip()[:60]
        ).strip("-")[:40] or "test-cases"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"TC_{slug}_{timestamp}_{tc_count}TC.xlsx"

        logger.info(
            "excel_generated_successfully",
            user_id=current_user.id,
            filename=filename,
            size_bytes=len(xlsx_bytes),
        )

        # Save to Google Drive (Shared Drive) instead of streaming the file down
        if payload.get("save_to_drive"):
            from app.services.drive_service import upload_xlsx, drive_enabled

            if not drive_enabled():
                raise HTTPException(
                    status_code=503,
                    detail="Google Drive export is not configured on the server (DRIVE_FOLDER_ID missing)",
                )
            uploaded = upload_xlsx(filename, xlsx_bytes)
            if session_obj is not None:
                session_obj.drive_file_link = uploaded["link"]
                await db.commit()
            logger.info(
                "excel_saved_to_drive",
                user_id=current_user.id,
                session_id=payload.get("session_id"),
                drive_link=uploaded["link"],
            )
            return {
                "saved_to_drive": True,
                "drive_link": uploaded["link"],
                "file_name": uploaded["name"],
            }

        return StreamingResponse(
            io.BytesIO(xlsx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "excel_generation_error",
            user_id=current_user.id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def _parse_llm_config(payload: dict) -> Union[str, LLMConfiguration]:
    """
    Parse LLM configuration from request payload.

    Supports:
    1. Simple mode: {"mode": "local_only" | "glm_only" | "combined"}
    2. Simple string model (backward compatible)
    3. Full LLMConfiguration object

    Returns:
        Either a string (model name) or LLMConfiguration
    """
    # Check for explicit llm_config
    if "llm_config" in payload:
        config_data = payload["llm_config"]

        # Handle dict input
        if isinstance(config_data, dict):
            # Check if using simple mode
            if "mode" in config_data:
                # Simple mode - just pass the dict, the router will resolve it
                return LLMConfiguration(**config_data)

            # Advanced mode - parse nested ModelConfig objects
            if "primary" in config_data and isinstance(config_data["primary"], dict):
                primary_data = config_data["primary"]
                config_data["primary"] = ModelConfig(**primary_data)

            if "secondary" in config_data and isinstance(config_data["secondary"], list):
                config_data["secondary"] = [
                    ModelConfig(**s) if isinstance(s, dict) else s
                    for s in config_data["secondary"]
                ]

            if "models_by_type" in config_data and isinstance(config_data["models_by_type"], dict):
                config_data["models_by_type"] = {
                    k: ModelConfig(**v) if isinstance(v, dict) else v
                    for k, v in config_data["models_by_type"].items()
                }

            return LLMConfiguration(**config_data)

        return config_data  # Already an LLMConfiguration

    # Check for simple model string
    if "model" in payload:
        return payload["model"]

    # Default to local_only mode
    return LLMConfiguration(mode="local_only")


def _model_config_to_cache_key(model_config: Union[str, LLMConfiguration]) -> str:
    """
    Convert model configuration to a cache key string.
    """
    if isinstance(model_config, str):
        return model_config

    # If simple mode is set, use it for the cache key
    if model_config.mode:
        parts = [
            f"mode:{model_config.mode.value}",
            f"local:{model_config.local_model}",
            f"glm:{model_config.glm_model}",
        ]
        return "|".join(parts)

    # Create a deterministic string representation for advanced config
    if not model_config.strategy or not model_config.primary:
        # Invalid config, use a default key
        return "unknown"

    parts = [
        model_config.strategy.value,
        model_config.primary.provider.value,
        model_config.primary.model,
        str(model_config.primary.weight),
    ]

    for secondary in model_config.secondary:
        parts.extend([
            secondary.provider.value,
            secondary.model,
            str(secondary.weight),
        ])

    # Add per-type overrides if present
    if model_config.models_by_type:
        parts.append("by_type:")
        for test_type, type_config in sorted(model_config.models_by_type.items()):
            parts.append(f"{test_type}:{type_config.provider.value}:{type_config.model}")

    return "|".join(parts)


def _model_config_to_string(model_config: Union[str, LLMConfiguration]) -> str:
    """
    Convert model configuration to a human-readable string for logging/storage.
    """
    if isinstance(model_config, str):
        return model_config

    # Handle simple mode
    if model_config.mode:
        mode_val = model_config.mode.value
        if mode_val == "local_only":
            return f"Local LLM ({model_config.local_model})"
        elif mode_val == "glm_only":
            return f"GLM API ({model_config.glm_model})"
        elif mode_val == "combined":
            return f"Combined (Local: {model_config.local_model} {int(model_config.local_weight*100)}% + GLM: {model_config.glm_model} {int(model_config.glm_weight*100)}%)"

    # Handle advanced config
    if model_config.strategy == MultiLLMStrategy.SINGLE:
        if model_config.models_by_type:
            types_str = ", ".join([
                f"{k}:{v.model}" for k, v in model_config.models_by_type.items()
            ])
            return f"Single (per-type: {types_str})"
        return f"Single ({model_config.primary.provider.value}/{model_config.primary.model})"

    elif model_config.strategy == MultiLLMStrategy.ENSEMBLE:
        models = [model_config.primary] + model_config.secondary
        models_str = ", ".join([f"{m.provider.value}/{m.model}" for m in models])
        return f"Ensemble ({models_str}) - {model_config.merge_method}"

    elif model_config.strategy == MultiLLMStrategy.CASCADE:
        models = [model_config.primary] + model_config.secondary
        models_str = ", ".join([f"{m.provider.value}/{m.model}" for m in models])
        return f"Cascade ({models_str})"

    return str(model_config)
