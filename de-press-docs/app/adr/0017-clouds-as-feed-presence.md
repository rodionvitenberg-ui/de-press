# Support Clouds as feed-row presence, not a list

A Support Cloud stays private (ADR 0008): it is never a public comment, like, or counter. The author does **not** see a list of clouds, a count, or a notification-bell item. The only author-facing signal is a quiet gesture on **their own feed row**, immediately before the row timestamp (`2m` / `5m`), driven by the latest unread Quiet Phrase (`i_am_here` sitting figure / `i_hear` heart / `not_alone` two figures). It fades in 1.5s, plays 4s, fades out 1.5s (7s total) without shifting layout; a click wiggles then dismisses. Opening the story marks the thread read; the row animation may finish its cycle. The story page itself is a Safe Monologue: no clouds, no reaction stickers, no counts under the post or author notes.

We rejected an author-private cloud list and a numeric unread badge because they recreate Pulse-as-showcase (already banned in the browser UI). Chat unread stays on the dialogue list, not the feed.

**Status:** accepted. Supersedes the author-UI reading of ADR 0008 (clouds as a page the author opens). The data model (private Support Cloud rows, one per sender × story) is unchanged.
