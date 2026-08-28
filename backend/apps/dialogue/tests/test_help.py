import pytest
from django.db import IntegrityError

from apps.dialogue.models import Dialogue, DialogueSource, HelpRequest, HelpRequestSkip
from apps.identity.models import Account, AnonymousSession


@pytest.mark.django_db
def test_help_request_one_pending_per_account():
    acc = Account.objects.create_user(email="u@ex.com", password="password123")
    HelpRequest.objects.create(from_account=acc, note="тихо")
    with pytest.raises(IntegrityError):
        HelpRequest.objects.create(from_account=acc, note="ещё")


@pytest.mark.django_db
def test_dialogue_help_allows_null_story():
    helper = Account.objects.create_user(
        email="h@ex.com", password="password123", is_helper=True
    )
    sess = AnonymousSession.objects.create(pseudonym="гость")
    d = Dialogue.objects.create(
        story=None,
        source=DialogueSource.HELP,
        author_session=sess,
        peer_account=helper,
    )
    assert d.story_id is None
    assert d.source == DialogueSource.HELP
