import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def cleanup():
    async with async_session_maker() as session:
        # Preview EN insights cu (affected_roles rong va published_at null)
        result = await session.execute(text(
            "SELECT id, title, impact_label, created_at "
            "FROM insights "
            "WHERE (affected_roles = '{}' OR affected_roles IS NULL) AND published_at IS NULL "
            "ORDER BY created_at"
        ))
        rows = result.fetchall()
        print(f"EN insights cu can xoa: {len(rows)}")
        for r in rows:
            print(f"  {str(r.id)[:8]} | {r.title[:55]} | {r.impact_label}")

        # Xoa chung
        del_result = await session.execute(text(
            "DELETE FROM insights "
            "WHERE (affected_roles = '{}' OR affected_roles IS NULL) AND published_at IS NULL "
            "RETURNING id"
        ))
        deleted = del_result.fetchall()
        await session.commit()
        print(f"\nDa xoa: {len(deleted)} insights EN cu")

        # Reset raw_documents tuong ung ve pending de re-analyze
        reset_result = await session.execute(text(
            "UPDATE raw_documents SET processing_status = 'pending', updated_at = now() "
            "WHERE processing_status = 'analyzed' "
            "AND id NOT IN (SELECT raw_document_id FROM insights) "
            "RETURNING id"
        ))
        reset_rows = reset_result.fetchall()
        await session.commit()
        print(f"Da reset: {len(reset_rows)} raw_documents -> pending")

asyncio.run(cleanup())
