# Monorepo: backend/ and frontend/ without shared tooling

We keep a single git repo with two top-level trees: `backend/` (Django) and `frontend/` (Next.js). No pnpm/npm workspaces, Turborepo, or shared package graph on day one — each side has its own dependency install and run commands. This is easy to reverse later if monorepo tooling pays off; starting without it avoids coupling Node and Python release cycles.
