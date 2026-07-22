# Contributing to AgentOpsLocal

Thanks for your interest in improving AgentOpsLocal! This guide covers everything you need to get productive quickly.

## Ways to Contribute

- 🐛 **Report bugs** — [open an issue](https://github.com/manijose1919/agent-ops-local/issues) with steps to reproduce.
- 💡 **Suggest features** — check the [Roadmap](./README.md#roadmap) first, then open an issue describing the use case.
- 📖 **Improve docs** — typo fixes and clarifications are always welcome.
- 🔧 **Submit code** — see the workflow below.

## Local Development Setup

See the [Local Development](./README.md#local-development) section of the README for full instructions. In short:

```bash
# Backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (second terminal)
npm install
npm run dev
```

## Development Workflow

1. **Fork** the repository and **clone** your fork.
2. **Create a branch** off `master`:
   ```bash
   git checkout -b feature/short-description
   ```
3. **Make your changes**, keeping them focused — one logical change per pull request.
4. **Add or update tests** for any backend behavior you change (see below).
5. **Run the checks** locally before pushing:
   ```bash
   pytest tests/        # backend tests
   npm run build        # frontend builds cleanly
   npm run lint         # frontend lint passes
   ```
6. **Commit** with a clear, imperative message (e.g. `Add p95 latency to summary endpoint`).
7. **Open a pull request** against `master` describing what changed and why.

The GitHub Actions CI pipeline runs the backend tests and a frontend build on every pull request — please make sure it's green.

## Coding Guidelines

- **Backend:** follow the existing FastAPI structure — routers in `backend/routers/`, ORM models in `backend/models.py`, Pydantic schemas in `backend/schemas.py`. Prefer pushing aggregation into SQL over looping in Python.
- **Frontend:** keep components in `src/`, style with Tailwind utility classes, and match the existing dark-theme design language.
- **Keep it focused:** avoid unrelated refactoring in a feature PR.

## Reporting Security Issues

Please do **not** open public issues for security vulnerabilities. Instead, report them privately to the maintainer.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
