from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthRepository:
    def create_refresh_session(
        self,
        db: Session,
        jti: str,
        user_id: str,
        expires_at_epoch: int,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        db.execute(
            text(
                """
                INSERT INTO refresh_token_sessions (jti, user_id, expires_at, user_agent, ip_address)
                VALUES (:jti, :user_id, to_timestamp(:expires_at_epoch), :user_agent, :ip_address)
                """
            ),
            {
                "jti": jti,
                "user_id": user_id,
                "expires_at_epoch": expires_at_epoch,
                "user_agent": user_agent,
                "ip_address": ip_address,
            },
        )

    def get_refresh_session(self, db: Session, jti: str) -> dict | None:
        return (
            db.execute(
                text(
                    """
                    SELECT jti, user_id, revoked_at
                    FROM refresh_token_sessions
                    WHERE jti = :jti
                    """
                ),
                {"jti": jti},
            )
            .mappings()
            .first()
        )

    def revoke_refresh_session(self, db: Session, jti: str, replaced_by_jti: str | None = None) -> int:
        result = db.execute(
            text(
                """
                UPDATE refresh_token_sessions
                SET revoked_at = now(), replaced_by_jti = :replaced_by_jti
                WHERE jti = :jti AND revoked_at IS NULL
                """
            ),
            {"jti": jti, "replaced_by_jti": replaced_by_jti},
        )
        return result.rowcount or 0

    def revoke_all_user_sessions(self, db: Session, user_id: str) -> None:
        db.execute(
            text(
                """
                UPDATE refresh_token_sessions
                SET revoked_at = now()
                WHERE user_id = :user_id AND revoked_at IS NULL
                """
            ),
            {"user_id": user_id},
        )


auth_repository = AuthRepository()
