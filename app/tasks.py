import time
from datetime import datetime, timezone

from app.celery_worker import celery_app


@celery_app.task(
    name="app.tasks.send_order_confirmation_email",
)
def send_order_confirmation_email(
    customer_email: str,
    order_id: int,
    total_amount: str,
) -> dict:
    """
    Simulate sending an order confirmation email.

    Replace this later with an actual email provider such as
    Amazon SES, SendGrid, Mailgun, or SMTP.
    """

    print("")
    print("=" * 60)
    print("ORDER CONFIRMATION EMAIL TASK STARTED")
    print(f"Customer email: {customer_email}")
    print(f"Order ID: {order_id}")
    print(f"Order total: {total_amount}")
    print("=" * 60)

    # Simulate a slow email provider.
    time.sleep(5)

    sent_at = datetime.now(timezone.utc).isoformat()

    print("")
    print("=" * 60)
    print("ORDER CONFIRMATION EMAIL SENT")
    print(f"To: {customer_email}")
    print(f"Order ID: {order_id}")
    print(f"Total: {total_amount}")
    print(f"Sent at: {sent_at}")
    print("=" * 60)
    print("")

    return {
        "status": "sent",
        "customer_email": customer_email,
        "order_id": order_id,
        "total_amount": total_amount,
        "sent_at": sent_at,
    }