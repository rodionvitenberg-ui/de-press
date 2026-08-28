# Optional Account plus AnonymousSession

Identity is dual: an optional `Account` (email/password) and a server-side `AnonymousSession` (UUID cookie) for Visitors who write or offer Silent Empathy. Stories and empathy rows reference exactly one author/source side. We rejected “accounts only” because the product is an anonymous quiet micro-blog, and “cookie-only signed tokens without server rows” because Empathy Pulse integrity needs durable de-duplication. Django's `User` model is customized as Account; public copy never says “user”.
