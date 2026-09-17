# AGENTS.md - Aquora Engineering Conventions & Guidelines

## Core Principles

1. **Strict Phase Boundaries**
   - Phase 0 establishes architecture, contracts, database models, Docker setup, and developer experience.
   - Do NOT implement real or fake hydrological calculations, synthetic predictions, or mock sensor streams until explicit future phases.

2. **Code Standards & Type Safety**
   - **TypeScript**: Use strict mode (`strict: true`) across all frontend code. No `any` types allowed.
   - **Python**: Use Python 3.11+ type hints across all backend components (`mypy` / strict typing).

3. **Architecture & Design**
   - **Modular Monolith**: Core services execute as a unified FastAPI monolith with async database and Redis communication.
   - **Engine & Provider Separation**:
     - Providers abstract external data acquisition.
     - Application Services coordinate workflows.
     - Engines contain pure hydrologic/geospatial computation logic.

4. **Security & Secrets**
   - Environment variables loaded via `pydantic-settings` on backend and `import.meta.env` on frontend.
   - **NEVER** commit API keys, database credentials, or secret tokens to source control.

5. **Testing Requirements**
   - All backend routes, database models, and service abstractions must be covered by `pytest` unit/integration tests.
   - Frontend must pass `tsc --noEmit` and Vite production build clean before completing any phase.

6. **Audit & Traceability**
   - Every state change or model run must be recorded in the `audit_events` or `model_runs` tables.
