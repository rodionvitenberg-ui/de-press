# Django Ninja instead of DRF

HTTP API uses Django Ninja with Pydantic schemas and explicit type hints. We preferred Ninja over Django REST Framework for smaller boilerplate and closer alignment with TypeScript DTO shapes on the frontend. DRF remains a valid alternative if we later need its ecosystem (browsable API, mature third-party packages); switching would be localized to `backend/api/`.
