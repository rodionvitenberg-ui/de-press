# Feed voice notes

Voice on Safe Monologues: a feed post (root or author follow-up) may be text, voice, or both.

Scope: `apps/browser` + Django `stories`. Mini App JSON publish stays text-only in this pass (same API still works). Dialogue voice is unchanged.

## Decisions

- **Where:** new post (`StoryComposer`) and author continuation (`StoryPage` composer). Guests still cannot write in the feed.
- **What:** text and/or voice. Empty text + empty audio is invalid.
- **Storage:** `Story.audio` FileField + `duration_ms`. No extra `StoryVoice` table.
- **STT:** same adapters as dialogue (`apps/dialogue/speech.py`). If the author did not type body, transcript is written to `body`. If they typed body, it is kept as-is (STT still runs only when body is empty).
- **API shape:** keep JSON `POST /api/v1/stories` and `POST /stories/{id}/comments` for text. Voice uses sibling endpoints (same pattern as dialogue):
  - `POST /api/v1/stories/voice` — Form: `body?`, `topic?`, `pseudonym?`, `duration_ms?`, `source_lang?` + File `audio`
  - `POST /api/v1/stories/{id}/comments/voice` — same Form/File, author-only
- **Edit:** `PATCH` still text-only. Audio is not replaced.
- **Delete/hide:** deleting a story deletes the file. Hide keeps the file (post can be unhidden).
- **Limits:** same as chat — 5 MiB, 120 s, 20 voice stories / window (reuse dialogue constants or a shared module).
- **List UI:** no player, no autoplay. Subtitle = typed body or a real transcript. If body is empty or an offline STT stub (`[офлайн…]` / `[offline…]`), show `Голосовое · 0:12` instead of the stub. Player (`VoiceBubble`) only on the open story/thread.
- **Anti-Panic:** pause/stop any playing feed audio (same as chat once panic kills the overlay world).
- **Recorder:** extract the MediaRecorder flow from `DialoguePage` into a shared hook used by chat + both feed composers. Reuse `VoiceBubble`.

## Model

`backend/apps/stories/models.py` `Story`:

- `audio` — `FileField(null=True, blank=True, upload_to=story_voice_upload_to)`
- `duration_ms` — `PositiveIntegerField(null=True, blank=True)`
- `body` — allow blank in the field; `clean` / service requires `body.strip() or audio`

Upload path: `story_voice/{story_id}.{ext}` (UUID known after pre-create, like dialogue).

`StoryOut` / browser `Story`: add `audio_url: string | null`, `duration_ms: number | null`.

WS `story.published` / `story.commented` / `story.updated` payloads include those fields so the live feed can show the mic mark without refetch.

## Services

`publish_story` / `add_comment`:

- If no audio: current text rules (body required).
- If audio: size/duration/rate-limit checks; save file; if `body` empty, `transcribe()` into body (offline stub is acceptable, same as chat).
- Reject empty body and no audio.

`delete_story`: `story.audio.delete(save=False)` then delete row.

## Browser

- `api.publishStoryVoice(blob, opts)` / `api.commentStoryVoice(postId, blob, opts)` — FormData, like `sendVoiceMessage`.
- Feed row: optional duration suffix; no `<audio>` in the list.
- `StoryPage` thread: `VoiceBubble` when `audio_url` is set; text still shown if body is real (not only an offline stub — show stub muted or hide stub and keep the player).
- Composer: mic next to submit; recording state replaces textarea until stop/cancel; allow keeping typed text and attaching the take.

## Tests

- Publish text-only still works (JSON).
- Publish voice-only: 201, `audio_url` set, body = STT stub in tests.
- Publish text+voice: body unchanged, audio stored.
- Empty both: 400.
- Oversize / too long: 400.
- Comment voice: non-author 403; author 201.
- Delete removes file from storage.
- Feed serializer includes `audio_url` / `duration_ms`.

## Out of scope

Mini App composer mic, replacing audio on edit, multiple files per post, autoplay, voice in guest clouds, store/native.
