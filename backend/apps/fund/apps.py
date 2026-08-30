from django.apps import AppConfig


class FundConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fund"
    label = "fund"
    verbose_name = "Duty Fund"