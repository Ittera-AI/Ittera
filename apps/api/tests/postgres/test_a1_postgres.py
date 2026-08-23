"""PostgreSQL-backed A1 migration and authorization contracts.

The fast API suite intentionally remains on in-memory SQLite. CI sets
``POSTGRES_TEST_DATABASE_URL`` after applying every Alembic migration so these
tests prove affected authorization and row-locking paths against the migrated
PostgreSQL schema. Local runs skip unless an explicit isolated test database is
supplied.
"""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from starlette.requests import Request

from app.core.permissions import Permission
from app.dependencies.workspace import get_current_workspace
from app.models.organization import (
    ApprovalDecision,
    ApprovalWorkflow,
    ContentApproval,
    Organization,
    Workspace,
    WorkspaceMember,
)
from app.models.user import User
from app.services import approval_service


@pytest.fixture()
def postgres_engine():
    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is required for PostgreSQL integration")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        pytest.fail(
            "POSTGRES_TEST_DATABASE_URL must reference an isolated PostgreSQL database"
        )

    engine = create_engine(database_url, poolclass=NullPool, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def postgres_db(postgres_engine) -> Session:
    connection = postgres_engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )
    session = testing_session()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


def _request_for_workspace(workspace_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": f"/api/v1/workspaces/{workspace_id}",
            "raw_path": f"/api/v1/workspaces/{workspace_id}".encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "root_path": "",
            "path_params": {"workspace_id": workspace_id},
        }
    )


@pytest.mark.asyncio
async def test_migrated_postgres_workspace_authorization_path(
    postgres_db: Session,
) -> None:
    suffix = uuid.uuid4().hex
    user = User(
        id=f"postgres-user-{suffix}",
        email=f"postgres-{suffix}@example.com",
        hashed_password="not-used",
        name="PostgreSQL A1 User",
    )
    organization = Organization(
        id=f"postgres-organization-{suffix}",
        name="PostgreSQL A1 Organization",
        slug=f"postgres-organization-{suffix}",
    )
    workspace = Workspace(
        id=f"postgres-workspace-{suffix}",
        organization=organization,
        name="PostgreSQL A1 Workspace",
        slug=f"postgres-workspace-{suffix}",
    )
    membership = WorkspaceMember(
        id=f"postgres-member-{suffix}",
        workspace=workspace,
        user=user,
        role="manager",
        permissions={"denied": [Permission.CONTENT_PUBLISH]},
    )
    postgres_db.add_all([user, organization, workspace, membership])
    postgres_db.flush()
    postgres_db.expire_all()

    resolved = await get_current_workspace(
        request=_request_for_workspace(workspace.id),
        x_workspace_id=None,
        current_user=postgres_db.get(User, user.id),
        db=postgres_db,
    )

    assert resolved is not None
    assert resolved.id == workspace.id
    resolved_member = resolved.get_member(user.id)
    assert resolved_member is not None
    assert resolved_member.has_permission(Permission.WORKSPACE_MANAGE)
    assert not resolved_member.has_permission(Permission.CONTENT_PUBLISH)


def test_postgres_serializes_competing_approval_decisions(postgres_engine) -> None:
    suffix = uuid.uuid4().hex
    user_id = f"approval-lock-user-{suffix}"
    organization_id = f"approval-lock-organization-{suffix}"
    workspace_id = f"approval-lock-workspace-{suffix}"
    member_id = f"approval-lock-member-{suffix}"
    workflow_id = f"approval-lock-workflow-{suffix}"
    approval_id = f"approval-lock-content-{suffix}"
    SessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)

    with SessionLocal() as seed:
        user = User(
            id=user_id,
            email=f"approval-lock-{suffix}@example.com",
            hashed_password="not-used",
            name="PostgreSQL Approval User",
        )
        organization = Organization(
            id=organization_id,
            name="PostgreSQL Approval Organization",
            slug=organization_id,
        )
        workspace = Workspace(
            id=workspace_id,
            organization=organization,
            name="PostgreSQL Approval Workspace",
            slug=workspace_id,
        )
        membership = WorkspaceMember(
            id=member_id,
            workspace=workspace,
            user=user,
            role="manager",
            permissions={},
        )
        workflow = ApprovalWorkflow(
            id=workflow_id,
            workspace=workspace,
            name="PostgreSQL Lock Workflow",
            content_type="post",
            steps=[
                {
                    "step_number": 1,
                    "role_required": "manager",
                    "title": "First review",
                },
                {
                    "step_number": 2,
                    "role_required": "manager",
                    "title": "Second review",
                },
            ],
            is_active=True,
        )
        approval = ContentApproval(
            id=approval_id,
            workspace=workspace,
            content_type="post",
            content_id=f"post-{suffix}",
            workflow=workflow,
            current_step=0,
            status="pending",
            requester=user,
        )
        seed.add_all(
            [user, organization, workspace, membership, workflow, approval]
        )
        seed.commit()

    contender_ready = Event()
    start_contender = Event()
    lock_attempted = Event()

    def note_lock_attempt(
        _conn,
        _cursor,
        statement,
        _parameters,
        _context,
        _executemany,
    ) -> None:
        if (
            current_thread().name.startswith("approval-contender")
            and "FOR UPDATE" in statement.upper()
        ):
            lock_attempted.set()

    def contend() -> tuple[int, str]:
        with SessionLocal() as contender_session:
            contender_approval = contender_session.get(ContentApproval, approval_id)
            contender_user = contender_session.get(User, user_id)
            assert contender_approval is not None
            assert contender_user is not None
            contender_ready.set()
            assert start_contender.wait(timeout=5)
            try:
                approval_service.make_decision(
                    db=contender_session,
                    approval=contender_approval,
                    approver=contender_user,
                    expected_step=0,
                    decision="approved",
                )
            except HTTPException as exc:
                contender_session.rollback()
                return exc.status_code, str(exc.detail)
            return 200, "unexpected success"

    event.listen(postgres_engine, "before_cursor_execute", note_lock_attempt)
    winner_session = SessionLocal()
    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="approval-contender",
    )
    future = None
    try:
        winner_approval = (
            winner_session.query(ContentApproval)
            .filter(ContentApproval.id == approval_id)
            .with_for_update()
            .one()
        )
        winner_user = winner_session.get(User, user_id)
        assert winner_user is not None

        future = executor.submit(contend)
        assert contender_ready.wait(timeout=5)
        start_contender.set()
        assert lock_attempted.wait(timeout=5)
        assert not future.done()

        winner_result = approval_service.make_decision(
            db=winner_session,
            approval=winner_approval,
            approver=winner_user,
            expected_step=0,
            decision="approved",
        )
        contender_status, contender_detail = future.result(timeout=10)

        assert winner_result.current_step == 1
        assert winner_result.status == "pending"
        assert contender_status == 409
        assert contender_detail == "Approval state changed; refresh and retry"

        with SessionLocal() as verify:
            persisted = verify.get(ContentApproval, approval_id)
            assert persisted is not None
            assert persisted.current_step == 1
            assert persisted.status == "pending"
            assert (
                verify.query(ApprovalDecision)
                .filter(ApprovalDecision.approval_id == approval_id)
                .count()
                == 1
            )
    finally:
        start_contender.set()
        winner_session.rollback()
        winner_session.close()
        executor.shutdown(wait=True, cancel_futures=True)
        event.remove(postgres_engine, "before_cursor_execute", note_lock_attempt)

        with SessionLocal() as cleanup:
            cleanup.query(ApprovalDecision).filter(
                ApprovalDecision.approval_id == approval_id
            ).delete(synchronize_session=False)
            cleanup.query(ContentApproval).filter(
                ContentApproval.id == approval_id
            ).delete(synchronize_session=False)
            cleanup.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.id == workflow_id
            ).delete(synchronize_session=False)
            cleanup.query(WorkspaceMember).filter(
                WorkspaceMember.id == member_id
            ).delete(synchronize_session=False)
            cleanup.query(Workspace).filter(Workspace.id == workspace_id).delete(
                synchronize_session=False
            )
            cleanup.query(Organization).filter(
                Organization.id == organization_id
            ).delete(synchronize_session=False)
            cleanup.query(User).filter(User.id == user_id).delete(
                synchronize_session=False
            )
            cleanup.commit()
