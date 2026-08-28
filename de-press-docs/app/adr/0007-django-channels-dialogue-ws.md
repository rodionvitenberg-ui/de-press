# Django Channels for Initiated Dialogue realtime

Dialogue messages use Django Channels over ASGI (Daphne) with a Redis channel layer in multi-process deploy, and InMemoryChannelLayer for SQLite/local tests. HTTP message APIs remain and broadcast into the same channel groups so REST and WS stay consistent. Auth is session cookie + optional `depress_anon` cookie via `ActorAuthMiddlewareStack`. Anti-Panic kills open browser sockets client-side. We rejected pure long-poll as the only transport once dialogue became a product core; Channels is the standard fit for Django ASGI.
