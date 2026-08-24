from app.config import Settings
from app.database.repository import Repository
from app.handlers.admin import create_admin_router
from app.handlers.user import create_user_router


def test_routers_build_without_network_call():
    settings = Settings(
        bot_token="test-token",
        supabase_url="https://example.supabase.co",
        supabase_key="test-key",
        admin_ids=frozenset({123}),
        restaurant_phone="+998 90 000 00 00",
        restaurant_address="Test",
    )
    repo = Repository(client=None)
    user_router = create_user_router(repo, settings)
    admin_router = create_admin_router(repo, settings)
    assert user_router.name == "user"
    assert admin_router.name == "admin"
    assert len(user_router.observers) > 0
    assert len(admin_router.observers) > 0
