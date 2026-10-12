
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from src.security import require_authenticated_user
from src.errors import ServiceError


def test_missing_authenticated_user_is_rejected():
    request = SimpleNamespace(state=SimpleNamespace())

    with pytest.raises(ServiceError) as exc:
        require_authenticated_user(request)

    assert exc.value.status_code == 401
    assert exc.value.error_code == "UNAUTHORIZED_USER"


def test_blank_authenticated_user_is_rejected():
    request = SimpleNamespace(
        state=SimpleNamespace(authenticated_user_id=" ")
    )

    with pytest.raises(ServiceError) as exc:
        require_authenticated_user(request)

    assert exc.value.status_code == 401


def test_verified_user_id_is_returned():
    request = SimpleNamespace(
        state=SimpleNamespace(authenticated_user_id="customer-1")
    )

    assert require_authenticated_user(request) == "customer-1"
