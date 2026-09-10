"""Revocable JWT epoch policy for supervisor and student identities.

Every newly-issued JWT carries the current epoch. Historical JWTs that predate
this rollout are interpreted as epoch 0 so rollout itself is non-destructive;
once a password/access code is rotated or an account activation state changes,
the durable epoch is atomically incremented and all earlier tokens become
invalid. No academic/history rows are modified.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session

from db.auth_models import AuthSessionState
from db.models import Student, User


def current_auth_epoch(db: Session, *, actor_role: str, actor_id: int) -> int:
    state = db.query(AuthSessionState).filter(
        AuthSessionState.actor_role == actor_role,
        AuthSessionState.actor_id == actor_id,
    ).first()
    return int(state.auth_epoch) if state is not None else 0


def token_epoch_matches(db: Session, *, actor_role: str, actor_id: int, token_epoch: object) -> bool:
    try:
        parsed = int(token_epoch if token_epoch is not None else 0)
    except (TypeError, ValueError):
        return False
    return parsed == current_auth_epoch(db, actor_role=actor_role, actor_id=actor_id)


def bump_auth_epoch(db: Session, *, actor_role: str, actor_id: int) -> int:
    """Explicitly revoke all earlier JWTs for one identity."""
    row = db.query(AuthSessionState).filter(
        AuthSessionState.actor_role == actor_role,
        AuthSessionState.actor_id == actor_id,
    ).with_for_update().first()
    if row is None:
        row = AuthSessionState(actor_role=actor_role, actor_id=actor_id, auth_epoch=1)
        db.add(row)
        db.flush()
        return 1
    row.auth_epoch = int(row.auth_epoch) + 1
    row.updated_at = datetime.now(timezone.utc)
    db.flush()
    return int(row.auth_epoch)


def _atomic_connection_bump(connection, *, actor_role: str, actor_id: int) -> None:
    # PostgreSQL and the supported SQLite test runtime both implement this UPSERT.
    connection.execute(
        text(
            """
            INSERT INTO auth_session_states (actor_role, actor_id, auth_epoch, updated_at)
            VALUES (:actor_role, :actor_id, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(actor_role, actor_id)
            DO UPDATE SET
                auth_epoch = auth_session_states.auth_epoch + 1,
                updated_at = CURRENT_TIMESTAMP
            """
        ),
        {"actor_role": actor_role, "actor_id": int(actor_id)},
    )


@event.listens_for(User, "after_update")
def _revoke_on_user_credential_or_activation_change(mapper, connection, target: User) -> None:
    state = inspect(target)
    if state.attrs.password_hash.history.has_changes() or state.attrs.is_active.history.has_changes():
        _atomic_connection_bump(connection, actor_role="researcher", actor_id=target.id)


@event.listens_for(Student, "after_update")
def _revoke_on_student_credential_or_activation_change(mapper, connection, target: Student) -> None:
    state = inspect(target)
    if state.attrs.access_code.history.has_changes() or state.attrs.is_active.history.has_changes():
        _atomic_connection_bump(connection, actor_role="student", actor_id=target.id)
