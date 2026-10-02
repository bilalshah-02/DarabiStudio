"""Order notification helpers — email sent via Brevo's HTTPS API (not SMTP,
since the hosting provider blocks outbound SMTP ports). WhatsApp only sends
if Twilio credentials are set in .env; both no-op silently if unconfigured
so the checkout flow never breaks because a notification failed.
"""
import logging
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send_via_brevo(to_email, subject, body_text):
    if not settings.BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not set — skipping email send")
        return
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "Darabi Studio"},
        subject=subject,
        text_content=body_text,
    )
    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException:
        logger.exception("Brevo API send failed")


def send_order_emails(order):
    context = {"order": order, "items": order.items.all()}

    if order.email:
        try:
            body = render_to_string("store/email/order_customer.txt", context)
            _send_via_brevo(order.email, f"Your Darabi Studio order {order.order_number}", body)
        except Exception:
            logger.exception("Failed to send customer order email")

    if settings.STORE_OWNER_EMAIL:
        try:
            body = render_to_string("store/email/order_owner.txt", context)
            _send_via_brevo(settings.STORE_OWNER_EMAIL, f"New order {order.order_number} — Rs. {order.total}", body)
        except Exception:
            logger.exception("Failed to send owner order email")


def send_order_whatsapp(order):
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.STORE_OWNER_WHATSAPP):
        return
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{settings.STORE_OWNER_WHATSAPP}",
            body=(f"New order {order.order_number} from {order.customer_name} "
                  f"({order.phone}) — Rs. {order.total} via {order.get_payment_method_display()}"),
        )
    except Exception:
        logger.exception("Failed to send WhatsApp order alert")
