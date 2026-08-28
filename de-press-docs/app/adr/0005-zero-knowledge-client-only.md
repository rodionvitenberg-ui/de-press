# Zero-Knowledge Memory stays on the client

Psychological profiling, mood tracking, and personal pattern graphs must not be synced to Django. Only device-local storage (IndexedDB) holds raw thoughts and emotional maps. The API must never accept endpoints that upload those payloads. Server may later proxy AI calls with ephemeral prompts, but must not persist emotional maps as user data.
