# План: паритет, дашборд хелпера, перевод, ретест (август 2026)

Смежные: [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md) (вопросы Q1–Q10), [ROADMAP.md](./ROADMAP.md), [VOICE_THERAPY_PLAN.md](./VOICE_THERAPY_PLAN.md) (закрыт).

Принципы: минимальные диффы; parity = перенос существующего, не новые фичи; каждый шаг заканчивается зелёными проверками и коммитом. Все вопросы решены 2026-08-30 — сводка в [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md) и «Решения фазы» [ROADMAP.md](./ROADMAP.md).

## P1. Хвосты паритета browser ↔ Mini App

| Шаг | Что | Статус |
|-----|-----|--------|
| P1.1 | **Терапия в Mini App**: TherapyPane + PayModal (Solana Pay QR), api-методы и типы (`TherapistProfileOut`/`TherapySession`/`Me.is_therapist`), i18n `therapy.*` (31 ключ) + `nav.therapy`, иконка в Sidebar-рельсе, `qrcode` dep | ✅ сделано |
| P1.2 | **Фонд в Mini App**: FundCard (закрытый диалог), TipBanner, TipWalletForm (UserMenu), `wallet.ts` + тест (решить: vitest в mini-app или общий пакет), api `fundInfo`/`setTipWallet`, i18n `fund.*` | следующий |
| P1.3 | **Calls в Mini App**: переносим (Q2) — call.* + signaling через dialogue-WS, feature-detect `navigator.mediaDevices` | после P1.2 |

Приёмка: `npm run build` (tsc + vite) в mini-app зелёный; i18n синхронно ru/en/types; суммарный каталог ≤ 640 ключей (общий кап `i18n_ui.MAX_KEYS`).

## P2. Публикация репозитория — в самом конце проекта (Q5)

Решение Q5: GitHub-публикация отложена до закрытия всех остальных задач проекта.
- В момент публикации: лицензия (AGPL-3.0), CI (GitHub Actions: ruff + pytest чанками, vitest, оба vite-билда), README (быстрый старт, стек, структура).
- Перед публикацией: `git log --format=%ae | sort -u` (email в истории), `.env.example` сверить с `settings/base.py`.

## P3. Перевод документации на EN

- Инвентарь: 15 доков в `de-press-docs/app` + 22 ADR + 6 в корне = **43 файла** (~2.6k строк).
- Сначала глоссарий (Q6), затем пачками: корень (README, PRIVACY, CONTEXT, MAINPLAN, PROGRESS) → app-доки → ADR.
- Формат: EN заменяет RU (решено Q6-A); перед переводом RU-версии копируются в `docs-ru-archive/` в корне проекта, папка в `.gitignore`.

## P4. Полный ретест

- **Backend** (чанками, ~30s таймаут раннера): therapy, fund, identity, common+notifications, dialogue, ai (`env -u DEEPSEEK_API_KEY`), empathy+moderation, support, stories.
- **Frontend:** browser vitest 64 + tsc + build; mini-app build.
- **Smoke-матрица** для ручной проверки (P6): антипаника · лента+облачка · тихие фразы · диалог+голос+кружочки · помощь human/AI · хелпер (очередь, дежурство, инвайты) · паттерны ZK · уведомления+`/inbox` · фонд (кошелёк/баннер/отчёт) · терапия (инвайт → каталог → сессия → QR → «я оплатил» → подтверждение → диалог) · переключение i18n · всё то же в Mini App внутри Telegram.

## P5. Хелперский дашборд

- Вкладка слева (browser), видна только `is_helper`; существующий `/helper` (HelperQueue) развивается в дашборд.
- Состав v1: живая очередь запросов по WS-каналу со старта (Q4; паттерн notifications-WS), «взять» → открытие диалога (кнопка звонка уже в диалоге), статус дежурства (существующий toggle), сводка (существующая), метрики из Q8.
- Инициирование беседы с хелпером пользователем — уже работает через запрос помощи; прямых звонков нет (Q7).
- Дизайн по токенам DESIGN_V2; backend-тесты на новые эндпоинты, если появятся.

## P6. Ручная QA

Критерии готовности: P1–P5 закрыты, smoke-матрица P4 отработана, известные ограничения записаны в PROGRESS. Дальше — пилот (pilot ops в ROADMAP).
