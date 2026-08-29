# Browser capabilities

Единая карта функций `@de-press/browser`. Бэкенд не вычищать: выключить = скрыть UI.

Статусы: `live` API+UI · `wired` есть в `client.ts`, UI молчит · `api` только сервер · `local` только устройство · `gap` дыра полировки.

Кандидат №1 на будущий off-ui: `chat.deleteMessage.everyone` (пир может стереть чужое). API оставить.

Кандидат №2: `empathy.outreach` (Написать / Случайному). Сомнительно. Бэкенд оставить.

## Mobile / PWA

| id | Что | Статус |
|---|---|---|
| `shell.phone` | ≤759px: список XOR экран (кроме `/feed/mine`), таб-бар Лента/Чаты/Уведомления/Ещё + panic | live |
| `shell.tablet` | 760–1099px: список + main, таб-бар, без рейла | live |
| `shell.desktop` | ≥1100px: рейл + split, без таб-бара | live |
| `shell.more` | `/more` — Паттерны, Помощь, Helper (роль), аккаунт, установка | live |
| `pwa.install` | манифест + standalone; CTA в «Ещё», без баннера | live |
| `pwa.sw` | шелл + `/assets/*`; **не** кэширует `/api`, `/ws`, `/media` | live |

Anti-Panic с таб-бара открывается так же, как с рейла. После первого визита шелл (и оверлей) открываются офлайн; лента/чат без сети пустые.

## Продуктовые запреты ленты

- Владелец **не** видит счётчик «сколько посидели молча». `empathy.pulse` с UI снят.
- «Лучи поддержки» в UI нет (ADR 0018). API `empathy.offer` жив, кнопок нет.
- Владельцу **нельзя** запрашивать чат и репортить свою запись.
- Гость шлёт **одно** облачко на историю (и одно на каждую авторскую запись внутри), не набор фраз.
- На странице записи **нет** облачков, стикеров чужих жестов и любых счётчиков — ни под постом, ни под записями.
- В ленте **нет** бейджа-числа облачков. Автору непрочитанное облачко — жест-анимация на **своей** строке (ADR 0017).
- Outreach-блок только если есть кому писать. Иначе секции нет.

## Auth

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `auth.register` | Регистрация | `POST /api/v1/auth/register` | UserMenu | live |
| `auth.login` | Вход | `POST /api/v1/auth/login` | UserMenu | live |
| `auth.logout` | Выход | `POST /api/v1/auth/logout` | UserMenu | live |
| `auth.me` | Кто я | `GET /api/v1/me` | Shell, UserMenu, StoryPage | live |
| `auth.inboxToken` | Magic-link inbox | `POST /api/v1/auth/inbox` | `/inbox?token=…` страница из письма | live |
| `auth.telegram` | Mini App initData | `POST /api/v1/auth/telegram` | нет (не browser) | api |

## Лента

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `feed.list` | Лента: **одна строка = один пост**; комментарии только внутри карточки | `GET /api/v1/stories` | FeedList | live |
| `story.comment` | Комментарий только автора к своему посту | `POST /api/v1/stories/{id}/comments` | StoryPage композер | live |
| `feed.live` | Живая лента, пока открыт `/feed` | `ws/feed/` | FeedList / StoryPage | live |
| `story.thread` | Монолог автора | `GET /api/v1/stories/{id}/thread` | StoryPage | live |
| `story.addNext` | Новая мысль в свою ленту (новая реакция, bump) | `POST /api/v1/stories` | композер внизу своей ленты | live |
| `feed.topics` | Справочник тем | `GET /api/v1/topics` | StoryComposer | live |
| `feed.filterTopic` | Лента по теме | `GET /api/v1/stories?topic=` | клиент шлёт `null` | wired |
| `feed.search` | Поиск | нет | фильтр уже загруженного | local |
| `story.read` | Открыть монолог | `GET /api/v1/stories/{id}` | StoryPage | live |
| `story.publish` | Написать | `POST /api/v1/stories` | StoryComposer | live |
| `story.publishVoice` | Голосовое к посту | `POST /api/v1/stories/voice` | StoryComposer mic | live |
| `story.commentVoice` | Голосовое в продолжении автора | `POST /api/v1/stories/{id}/comments/voice` | StoryPage mic | live |
| `story.edit` | Править свой монолог | `PATCH /api/v1/stories/{id}` | StoryPage владелец | live |
| `story.hide` | Скрыть свою запись | `POST /api/v1/stories/{id}/hide` | ПКМ своей строки | live |
| `story.unhide` | Показать снова | `POST /api/v1/stories/{id}/unhide` | Моя история / ПКМ | live |
| `story.delete` | Удалить запись | `DELETE /api/v1/stories/{id}` | ПКМ своей строки | live |
| `story.mine` | Моя история | `GET /api/v1/me/stories` | `/feed/mine` | live |
| `feed.rowMenu` | ПКМ по строке ленты | — | FeedMenu | live |

## Лучи / облачка / запрос

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `empathy.offer` | Лучи | `POST /api/v1/stories/{id}/empathy` | API жив, **UI снят** (ADR 0018) | wired |
| `empathy.pulse` | Pulse-счётчик | `GET /api/v1/stories/{id}/pulse` | API жив, **UI запрещён** | wired |
| `empathy.hearers` | Кто услышал | `GET /api/v1/stories/{id}/hearers` | только если есть кому писать | live |
| `empathy.outreachConsent` | Opt-out outreach | `POST …/empathy/outreach-consent` | client | wired |
| `empathy.outreach` | Написать / Случайному | `POST /api/v1/stories/{id}/outreach` | только если есть кому; **сомнительно, off-ui кандидат** | live |
| `cloud.phrases` | Каталог облачков | `GET /api/v1/quiet-phrases` | три жеста, один тап | live |
| `cloud.image` | Картинка фразы | `QuietPhrase.image` | API есть, UI ленты не показывает | wired |
| `cloud.onePerSender` | Одно облачко на story×actor | unique + reject | QuietPhrases | live |
| `cloud.freeText` | Своё облачко | `POST …/clouds` `{body}` | Helper / модерация; в ленте нет формы | wired |
| `cloud.list` | Облачка автору | `GET …/clouds` | API жив, **UI запрещён** (ADR 0017) | wired |
| `cloud.dismiss` | Закрыть облачко у себя | `POST …/clouds/{id}/dismiss` | API жив, UI снят | wired |
| `cloud.feedGesture` | Жест на своей строке ленты | `Story.cloud_gesture` + mark-read | 1.5s in + 4s play + 1.5s out; клик — шевеление; слот до таймера, без сдвига вёрстки | live |
| `cloud.inbox` | support_cloud в колокольчике | Notification row | **скрыт**, как MESSAGE | wired |
| `dialogue.request` | Запрос диалога | `POST /api/v1/stories/{id}/dialogue-requests` | StoryPage | live |
| `dialogue.intents` | Intent | `GET /api/v1/dialogue/intents` | форма запроса | live |

## Чат — список

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `chat.list` | Мои диалоги | `GET /api/v1/me/dialogues` | ChatList | live |
| `chat.getOne` | Один диалог | `GET /api/v1/dialogues/{id}` | DialoguePage `loadMeta` | live |
| `chat.inbox` | Запросы | `GET /api/v1/me/dialogue-requests` | ChatList | live |
| `chat.accept` | Принять запрос | `POST /api/v1/dialogue-requests/{id}/accept` | ChatList | live |
| `chat.decline` | Отклонить | `POST /api/v1/dialogue-requests/{id}/decline` | ChatList | live |
| `chat.pin` | Закрепить чат | `POST …/pin-chat` | ChatMenu | live |
| `chat.unpin` | Открепить | `POST …/unpin-chat` | ChatMenu | live |
| `chat.mute` | Заглушить | `POST …/mute` | ChatMenu | live |
| `chat.unmute` | Включить звук | `POST …/unmute` | ChatMenu | live |
| `chat.markRead` | Прочитано | `POST …/mark-read` | ChatMenu + открытие треда | live |
| `chat.markUnread` | Непрочитанное | `POST …/mark-unread` | ChatMenu | live |
| `chat.clearHistory` | Очистить историю | `POST …/clear-history` `me\|everyone` | ChatMenu | live |
| `chat.delete` | Удалить чат | `DELETE /api/v1/dialogues/{id}?scope=` | ChatMenu | live |
| `chat.block` | Блок пира | `POST …/block-peer` | ChatMenu | live |
| `chat.unblock` | Разблок | `POST …/unblock-peer` | ChatMenu | live |
| `chat.close` | Закрыть диалог | `POST …/close` | шапка треда | live |
| `chat.reopen` | Открыть снова | `POST …/reopen` | шапка треда | live |

## Чат — тред

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `chat.ws` | Live | `WS /ws/dialogues/{id}/` | useChatSocket; HTTP 4s fallback | live |
| `chat.messages` | История | `GET /api/v1/dialogues/{id}/messages` | fallback + prefetch | live |
| `chat.send` | Текст | `POST …/messages` + WS | composer | live |
| `chat.reply` | Ответ | `reply_to_id` | MessageMenu | live |
| `chat.edit` | Правка своего | `PATCH /api/v1/messages/{id}` | MessageMenu | live |
| `chat.copy` | Копировать | нет | clipboard | local |
| `chat.forward` | Переслать | `POST /api/v1/messages/{id}/forward` | MessageMenu | live |
| `chat.pinMessage` | Пин сообщения | `POST …/pin` `…/unpin` | MessageMenu + pin bar | live |
| `chat.translate` | Перевод | `POST /api/v1/messages/{id}/translate` | MessageMenu | live |
| `chat.transcribe` | Повторный STT | `POST /api/v1/messages/{id}/transcribe` | нет (UI снят, авто-STT скрыт) | api |
| `chat.voice` | Голосовое | `POST …/messages/voice` | mic | live |
| `chat.circle` | Кружок | `POST …/messages/circle` | кнопка в поле | live |
| `chat.voiceRetention` | Хранить голос | `GET/POST /api/v1/me/voice-retention` | UserMenu | live |
| `chat.deleteMessage.me` | Удалить у себя | `DELETE /api/v1/messages/{id}?scope=me` | MessageMenu | live |
| `chat.deleteMessage.everyone` | Удалить у всех | `DELETE …?scope=everyone` | MessageMenu; пир может стереть чужое | live |
| `chat.reportMessage` | Репорт сообщения | `POST /api/v1/messages/{id}/report` | MessageMenu; help-чат без Story | live |
| `chat.reportStory` | Репорт истории | `POST /api/v1/stories/{id}/report` | StoryPage ⋯ | live |
| `chat.typing` | Печатает | WS | три точки | live |

События WS треда: message, edited, deleted, pinned, closed, reopened, typing.

## Прочее

| id | Что | Backend | Browser | Статус |
|---|---|---|---|---|
| `notify.list` | Уведомления | `GET /api/v1/me/notifications` | NotificationsPane | live |
| `notify.unread` | Бейдж | `GET …/unread-count` + WS | Sidebar | live |
| `notify.ws` | Live notify | `WS /ws/notifications/` | useNotifications | live |
| `notify.mark` | Прочитать одно | `POST …/{id}/read` | pane | live |
| `notify.markAll` | Прочитать все | `POST …/read-all` | pane | live |
| `notify.settings` | Почта / дайджест | `GET/POST /api/v1/me/notify-settings` | client | wired |
| `notify.testEmail` | Тест дайджеста | `POST …/notify-settings/test` | client | wired |
| `notify.testTelegram` | Тест TG | `POST …/test-telegram` | нет в client | api |
| `helper.queue` | Очередь облачков | `GET /api/v1/moderation/clouds` + approve/reject | HelperQueue | live |
| `helper.dialogueReview` | Проверка Dialogue Request | `GET/POST /api/v1/moderation/dialogue-requests*` | ChatList grey rows | live |
| `helper.invite` | Инвайт Helperа | `POST /api/v1/helper-invites` | UserMenu + `/helper/invite` | live |
| `helper.join` | Принять инвайт | `POST /api/v1/helper-invites/{token}/accept` | `/helper/join?token=` | live |
| `helper.dashboard` | Ops-метрики | `GET /api/v1/moderation/dashboard` | /helper вкладка Сводка | live |
| `moderation.blocks` | Общий блок | `POST /api/v1/blocks` | нет (блок через чат) | api |
| `ai.support` | DeepSeek | `POST /api/v1/ai/support` | client + CompanionPane live; Anti-Panic не зовёт | live |
| `panic.overlay` | Anti-Panic | нет | overlay, рвёт WS | local |
| `patterns.local` | ZK паттерны | нет | IndexedDB | local |
| `help.static` | Помощь | нет | HelpPane | local |
| `help.human` | Путь «человек рядом» | `POST /api/v1/help/requests` | HelpPane → wait | live |
| `help.wait` | Ожидание ответа Helper | `GET …/help/requests/mine` | `/help/wait` | live |
| `help.ai` | Компаньон-чат | `POST /api/v1/ai/support` | `/help/ai` CompanionPane | live |
| `help.request` | Запрос помощи | API + UI | HelpPane / ChatList | live (API+UI) |
| `helper.helpInbox` | Inbox запросов Helper | `GET /api/v1/help/requests` | ChatList grey rows | live |
| `helper.duty` | Дежурство Helperа | `POST /api/v1/me/helper-duty` + `GET /me` `is_on_duty` | /helper тумблер + UserMenu | live |
| `shell.theme` | Тема | нет | UserMenu | local |
| `shell.locale` | Язык | нет | UserMenu | local |
| `shell.navOrder` | Порядок rail | нет | localStorage | local |
| `health` | Healthcheck | `GET /api/v1/health` | не в UI | api |
