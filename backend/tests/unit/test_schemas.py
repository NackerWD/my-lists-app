"""Tests unitaris per als schemas Pydantic — cap connexió a BD ni a Supabase."""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.activity_log import ActivityLogCreate, ActivityLogResponse
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.device_token import DeviceTokenCreate
from app.schemas.list import ListCreate, ListUpdate
from app.schemas.list_invitation import ListInvitationCreate, ListInvitationUpdate
from app.schemas.list_item import ListItemCreate, ListItemUpdate
from app.schemas.list_member import ListMemberCreate, ListMemberUpdate
from app.schemas.list_type import ListTypeCreate, ListTypeUpdate


class TestAuthSchemas:
    def test_register_valid(self) -> None:
        r = RegisterRequest(email="user@example.com", password="password12345")
        assert r.email == "user@example.com"

    def test_register_password_too_short(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="short")

    def test_register_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password12345")

    def test_login_valid(self) -> None:
        r = LoginRequest(email="user@example.com", password="any")
        assert r.email == "user@example.com"

    def test_token_response_defaults(self) -> None:
        t = TokenResponse(access_token="abc", refresh_token="def")
        assert t.token_type == "bearer"
        assert t.expires_in == 900


class TestListSchemas:
    def test_list_create_valid(self) -> None:
        data = ListCreate(title="La meva llista")
        assert data.title == "La meva llista"
        assert data.is_archived is False
        assert data.description is None

    def test_list_create_with_type(self) -> None:
        lid = uuid.uuid4()
        data = ListCreate(title="Compra", list_type_id=lid)
        assert data.list_type_id == lid

    def test_list_update_partial(self) -> None:
        data = ListUpdate(title="Nou títol")
        assert data.title == "Nou títol"
        assert data.is_archived is None


class TestListItemSchemas:
    def test_list_item_create_defaults(self) -> None:
        data = ListItemCreate(content="Comprar llet")
        assert data.is_checked is False
        assert data.priority is None
        assert data.position == 0  # defecte és 0, no None

    def test_list_item_priority_valid_values(self) -> None:
        for priority in ["high", "medium", "low"]:
            data = ListItemCreate(content="test", priority=priority)
            assert data.priority == priority

    def test_list_item_priority_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ListItemCreate(content="test", priority="urgent")  # type: ignore[arg-type]

    def test_list_item_update_partial(self) -> None:
        data = ListItemUpdate(is_checked=True)
        assert data.is_checked is True
        assert data.content is None


class TestListMemberSchemas:
    def test_member_create_defaults(self) -> None:
        data = ListMemberCreate(user_id=uuid.uuid4())
        assert data.role == "viewer"

    def test_member_update_valid_roles(self) -> None:
        for role in ["owner", "editor", "viewer"]:
            data = ListMemberUpdate(role=role)
            assert data.role == role

    def test_member_update_invalid_role(self) -> None:
        with pytest.raises(ValidationError):
            ListMemberUpdate(role="admin")  # type: ignore[arg-type]


class TestListInvitationSchemas:
    def test_invitation_create(self) -> None:
        # ListInvitationCreate només té camp email (no list_id)
        data = ListInvitationCreate(email="invited@example.com")
        assert data.email == "invited@example.com"

    def test_invitation_create_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            ListInvitationCreate(email="not-an-email")

    def test_invitation_update_valid_statuses(self) -> None:
        for status in ["pending", "accepted", "expired"]:
            data = ListInvitationUpdate(status=status)
            assert data.status == status


class TestDeviceTokenSchemas:
    def test_valid_platforms(self) -> None:
        # DeviceTokenCreate NO té camp user_id
        for platform in ["ios", "android", "web"]:
            data = DeviceTokenCreate(token="tok123", platform=platform)
            assert data.platform == platform

    def test_invalid_platform(self) -> None:
        with pytest.raises(ValidationError):
            DeviceTokenCreate(token="tok", platform="windows")  # type: ignore[arg-type]


class TestListTypeSchemas:
    def test_list_type_create(self) -> None:
        data = ListTypeCreate(slug="todo", label="Tasques")
        assert data.slug == "todo"
        assert data.is_active is True

    def test_list_type_update_partial(self) -> None:
        data = ListTypeUpdate(label="Nou label")
        assert data.label == "Nou label"
        assert data.icon is None


class TestUserSchemas:
    def test_user_create_valid(self) -> None:
        from app.schemas.user import UserCreate

        data = UserCreate(email="user@example.com", display_name="Joan")
        assert data.email == "user@example.com"
        assert data.display_name == "Joan"
        assert data.avatar_url is None

    def test_user_update_partial(self) -> None:
        from app.schemas.user import UserUpdate

        data = UserUpdate(display_name="Nou Nom")
        assert data.display_name == "Nou Nom"
        assert data.avatar_url is None

    def test_user_response_from_attributes(self) -> None:
        from unittest.mock import MagicMock

        from app.schemas.user import UserResponse

        obj = MagicMock()
        obj.id = uuid.uuid4()
        obj.email = "resp@example.com"
        obj.display_name = "Test"
        obj.avatar_url = None
        obj.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        obj.last_seen_at = None
        resp = UserResponse.model_validate(obj)
        assert resp.email == "resp@example.com"


class TestActivityLogSchemas:
    def test_activity_log_create(self) -> None:
        data = ActivityLogCreate(action="item_added", list_id=uuid.uuid4())
        assert data.action == "item_added"
        assert data.payload is None
        assert data.user_id is None

    def test_activity_log_create_with_payload(self) -> None:
        data = ActivityLogCreate(
            action="item_updated",
            list_id=uuid.uuid4(),
            payload={"item_id": "abc"},
        )
        assert data.payload == {"item_id": "abc"}

    def test_activity_log_response_from_attributes(self) -> None:
        from unittest.mock import MagicMock
        obj = MagicMock()
        obj.id = uuid.uuid4()
        obj.list_id = uuid.uuid4()
        obj.user_id = None
        obj.action = "test"
        obj.payload = None
        obj.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        resp = ActivityLogResponse.model_validate(obj)
        assert resp.action == "test"
