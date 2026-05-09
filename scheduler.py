import uuid
from datetime import datetime
from sqlalchemy import text
from src.renderer import render_email


def ensure_datetime(value):
    """
    Converts ISO string / datetime / None → datetime or None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def plan_next_fires(db, now):
    # normalize now just in case
    now = ensure_datetime(now)

    rows = db.execute(text("""
        SELECT id, contact_id, campaign_id, start_at_utc, last_fired_at_utc
        FROM reminders
        WHERE active = 1
    """)).fetchall()

    for r in rows:
        start_at = ensure_datetime(r.start_at_utc)
        last_fired = ensure_datetime(r.last_fired_at_utc)

        # only fire if never fired AND start time reached
        if last_fired is None and start_at and start_at <= now:
            mid = str(uuid.uuid4())

            db.execute(text("""
                INSERT INTO messages(id, campaign_id, contact_id, scheduled_at_utc, status)
                VALUES (:id, :cid, :ct, :sch, 'scheduled')
            """), {
                "id": mid,
                "cid": r.campaign_id,
                "ct": r.contact_id,
                "sch": now
            })

            db.execute(text("""
                UPDATE reminders
                SET last_fired_at_utc = :now
                WHERE id = :rid
            """), {
                "now": now,
                "rid": r.id
            })


async def dispatch_due(db, mailer, now):
    now = ensure_datetime(now)

    rows = db.execute(text("""
        SELECT m.id, c.email, c.name, t.subject, t.body_md,
               camp.sender_name, camp.sender_email
        FROM messages m
        JOIN contacts c ON c.id = m.contact_id
        JOIN campaigns camp ON camp.id = m.campaign_id
        JOIN templates t ON t.id = camp.template_id
        WHERE m.status = 'scheduled'
    """)).fetchall()

    for r in rows:
        subject, html = render_email(
            r.subject,
            r.body_md,
            {"name": r.name}
        )

        res = await mailer.send_email(
            r.sender_name,
            r.sender_email,
            r.email,
            subject,
            html
        )

        if res["ok"]:
            print(f"✅ Email sent to {r.email}")

            db.execute(text("""
                UPDATE messages
                SET status='sent', sent_at_utc=:now
                WHERE id=:id
            """), {"now": now, "id": r.id})

        else:
            print(f"❌ Failed: {res['error']}")

            db.execute(text("""
                UPDATE messages
                SET status='failed', error=:err
                WHERE id=:id
            """), {
                "err": res["error"],
                "id": r.id
            })
            