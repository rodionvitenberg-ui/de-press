# CLAUDE.md — de-press.co Guidelines

## 📌 Overview
`de-press.co` is an empathetic, non-commercial mental health platform and safe haven
(quiet monologues, silent empathy, Anti-Panic, zero-knowledge local patterns).

**Three independent frontends + one backend (all Vite + React SPA; no Next.js):**
- `apps/browser/` — browser only (no Telegram Web A / no Mini App bridge)
- `apps/mini-app/` — Mini App; target shell = Telegram Web A (`vendor/telegram-tt`, GPLv3)
- `apps/admin/` — staff/admin panel
- `packages/api-client/` — shared API client (`@de-press/api-client`), re-exported by both frontends (ADR 0023); regen types: `npm run gen:api`
Never import mini-app vendor into browser. See `apps/README.md`, ADR 0014.
Legacy Next: `_archive/legacy/next-frontend/` (archived). Django: `backend/apps/`.

---

## 🛠 Tech Stack
- **Frontend:** Vite + React (TypeScript) — three independent SPAs. No Next.js (archived legacy only).
- **Backend:** Python / Django (Django Ninja for REST + Django Channels for WebSockets)
- **Database & Cache:** PostgreSQL (primary DB) + Redis (cache, rate limits, Channels layer; optional in dev)
- **Styling:** CSS Modules (`*.module.css`) + Native CSS Custom Properties (Design Tokens in `<app>/src/styles/tokens.css`). **STRICTLY NO TAILWIND CSS.**
- **Local Storage:** IndexedDB (for Zero-Knowledge personal emotional patterns)
- **AI Integration:** DeepSeek API (proxied via Django API Gateway)

---

## 🎨 Styling Rules & Design Tokens
1. **Strictly No Utility CSS Frameworks:** Do not use Tailwind, UnoCSS, or inline utility styles.
2. **CSS Modules:** Every component must have a dedicated `.module.css` file (e.g., `Button.module.css`).
3. **Design Tokens:** Always reference semantic CSS variables from the app's `src/styles/tokens.css` (`apps/browser`, `apps/mini-app`; admin styles live in `apps/admin/src/admin.css`):
   - Colors: `var(--bg-main)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--text-muted)`, `var(--accent-hope)`
   - Spacing & Radii: `var(--space-2)`, `var(--space-4)`, `var(--radius-md)`, `var(--btn-padding)`
4. **Naming Convention:** Use camelCase for CSS module classes (e.g., `styles.btnPrimary`, `styles.cardContainer`).

---

## 🏛 Core Domain Terminology & Principles
- **Anti-Panic Protocol:** A global, high-priority emergency UI mode ("Мне хуево, отвали" — "I'm not ok, leave me alone") that instantly kills WebSocket connections, hides analytics/feeds, and activates a minimal canvas for 4-7-8 breathing and somatic grounding.
- **Silent Empathy:** Interaction without likes, upvotes, or public counters. Users can only send "Я слышу тебя" (I hear you). Authors see a subtle pulse: "3 people read this and sat with you silently."
- **Safe Monologue:** Stories published without public comment sections to prevent unsolicited advice and cyberbullying.
- **Initiated Dialogue:** Anonymous 1-on-1 chat over Django Channels that can **only** be initiated by the story author.
- **Zero-Knowledge Memory:** All psychological profiling, mood tracking, and personal pattern analysis **must strictly stay inside IndexedDB on the user's device**. Never sync raw user thoughts or emotional maps to the Django server.

---

## 🤖 AI Prompting Rules (No Toxic Positivity)
When writing system prompts or AI integrations with DeepSeek:
- **FORBIDDEN:** Toxic positivity ("Everything will be great!", "Just cheer up!"), medical diagnosing, giving unsolicited life advice.
- **REQUIRED:** Emotional validation ("What you feel is completely understandable"), reflective questions, highlighting recurring cycles *only when explicitly requested by the user*.

---

## 💻 Code Style & Architecture
- **TypeScript:** Strict mode enabled on Frontend. Define explicit interfaces for all Props, API responses, and Domain models.
- **Python / Django:** PEP8 compliant, type hints, clean serializers/schemas, decoupled ASGI WebSocket consumers.
- **Component Architecture:** Keep TSX files clean. Separate presentation from heavy logic via custom hooks (`useAntiPanic`, `useLocalMemory`, `useChatSocket`).
- **Imports Order (Frontend):**
  1. React / React Router core
  2. Third-party libraries (react-query, etc.)
  3. API services & custom hooks
  4. Internal components
  5. Styles (`import styles from './Component.module.css'`)

---

## 🚀 Development Commands
```bash
# Frontend — per app (apps/browser, apps/mini-app, apps/admin)
cd apps/browser && npm run dev   # local dev server
npm run build                    # production build check (tsc -b && vite build)
npm test                         # vitest (apps/browser, apps/mini-app)

# Backend (Django, from backend/)
python manage.py runserver     # Run Django API & ASGI WebSocket server
python manage.py migrate       # Apply database migrations
```