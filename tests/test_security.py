from http import HTTPStatus

import pytest
from fastapi import HTTPException

from lnbits.core.models.payments import Payment, PaymentState
from lnbits.extensions.wasm.views_api import (
    _ensure_payment_tags_allowed,
    _ensure_payments_policy_required,
    _parse_api_permission,
)
from lnbits.extensions.wasm.wasm_host.extension_host import (
    _apply_payment_extra_updates,
    _check_quota,
    _enforce_payments_policy_proxy,
)


def test_parse_api_permission_requires_api_prefix_and_absolute_path():
    assert _parse_api_permission("api.POST:/api/v1/payments") == (
        "POST",
        "/api/v1/payments",
    )
    assert _parse_api_permission("POST:/api/v1/payments") is None
    assert _parse_api_permission("api.POST:api/v1/payments") is None


def test_payment_tag_grants_are_strictly_declared():
    with pytest.raises(HTTPException) as exc:
        _ensure_payment_tags_allowed([], ["undeclared"])
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(HTTPException) as exc:
        _ensure_payment_tags_allowed(["paidtasks"], [])
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(HTTPException) as exc:
        _ensure_payment_tags_allowed(["paidtasks"], ["other"])
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    _ensure_payment_tags_allowed(["paidtasks"], ["paidtasks"])


def test_payments_api_permission_requires_explicit_direction_policy():
    with pytest.raises(HTTPException) as exc:
        _ensure_payments_policy_required([{"id": "api.POST:/api/v1/payments"}])
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(HTTPException) as exc:
        _ensure_payments_policy_required(
            [
                {
                    "id": "api.POST:/api/v1/payments",
                    "policy": {"payments_out": "false"},
                }
            ]
        )
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    _ensure_payments_policy_required(
        [{"id": "api.POST:/api/v1/payments", "policy": {"payments_out": False}}]
    )


def test_payment_proxy_requires_out_and_enforces_policy(monkeypatch):
    monkeypatch.setattr(
        "lnbits.extensions.wasm.wasm_host.extension_host._load_http_permission_policies",
        lambda ext_id: {("POST", "/api/v1/payments"): {"payments_out": False}},
    )

    with pytest.raises(HTTPException) as exc:
        _enforce_payments_policy_proxy("paidtasks", "POST", "/api/v1/payments", {})
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(HTTPException) as exc:
        _enforce_payments_policy_proxy(
            "paidtasks", "POST", "/api/v1/payments", {"out": "false"}
        )
    assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(HTTPException) as exc:
        _enforce_payments_policy_proxy(
            "paidtasks", "POST", "/api/v1/payments", {"out": True}
        )
    assert exc.value.status_code == HTTPStatus.FORBIDDEN

    _enforce_payments_policy_proxy(
        "paidtasks", "POST", "/api/v1/payments", {"out": False}
    )


@pytest.mark.anyio
async def test_paidtasks_fallback_only_marks_task_paid_after_full_amount(monkeypatch):
    applied_updates = []

    async def fake_kv_get(db, ext_id, key):
        assert ext_id == "paidtasks"
        assert key == "task_cost:task-1"
        return "100"

    async def fake_apply_list_updates(db, ext_id, updates):
        applied_updates.extend(updates)

    monkeypatch.setattr(
        "lnbits.extensions.wasm.wasm_host.extension_host._kv_get", fake_kv_get
    )
    monkeypatch.setattr(
        "lnbits.extensions.wasm.wasm_host.extension_host._apply_list_updates",
        fake_apply_list_updates,
    )

    underpaid = _payment(amount_msat=99_000)
    await _apply_payment_extra_updates(None, "paidtasks", underpaid, "task_paid:task-1")
    assert applied_updates == []

    paid = _payment(amount_msat=100_000)
    await _apply_payment_extra_updates(None, "paidtasks", paid, "task_paid:task-1")
    assert applied_updates == [
        {"key": "tasks", "id": "task-1", "field": "paid", "value": True},
        {"key": "public_tasks", "id": "task-1", "field": "paid", "value": True},
    ]


def test_quota_defaults_to_deny_after_limit():
    user_id = "quota-user"
    ext_id = "quota-ext"
    _check_quota(user_id, ext_id, "db", 1)
    with pytest.raises(HTTPException) as exc:
        _check_quota(user_id, ext_id, "db", 1)
    assert exc.value.status_code == HTTPStatus.TOO_MANY_REQUESTS


def _payment(amount_msat: int) -> Payment:
    return Payment(
        checking_id="checking",
        payment_hash="hash",
        wallet_id="wallet",
        amount=amount_msat,
        fee=0,
        bolt11="bolt11",
        status=PaymentState.SUCCESS.value,
        extra={},
    )
