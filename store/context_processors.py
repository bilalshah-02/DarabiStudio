import os


def site_settings(request):
    """Global values available in every template — edit these via .env
    (STORE_WHATSAPP_NUMBER, STORE_CONTACT_EMAIL, STORE_INSTAGRAM_URL) so the
    owner can update contact details without touching template code.
    """
    whatsapp_number = os.environ.get("STORE_WHATSAPP_NUMBER", "").strip()
    return {
        "STORE_NAME": "Darabi Studio",
        "STORE_WHATSAPP": os.environ.get("STORE_WHATSAPP_DISPLAY", "+92 3XX XXXXXXX"),
        "STORE_WHATSAPP_LINK": f"https://wa.me/{whatsapp_number}" if whatsapp_number else "",
        "STORE_EMAIL": os.environ.get("STORE_CONTACT_EMAIL", "hello@darabistudio.pk"),
        "STORE_INSTAGRAM": os.environ.get("STORE_INSTAGRAM_URL", "https://instagram.com/darabistudio.pk"),
    }
