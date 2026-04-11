import re
from urllib.parse import urlparse, parse_qs
from django.core.exceptions import ValidationError

ALLOWED_HOSTS = {"www.google.com", "google.com"}
EMBED_PATH = "/maps/embed"


def validate_google_maps_embed_url(value: str):
    if not value:
        return

    value = value.strip()

    # Reject iframe or any HTML
    if "<" in value or ">" in value:
        raise ValidationError("Only a Google Maps embed URL is allowed (no HTML/iframe).")

    # Basic URL sanity check
    if not value.startswith(("http://", "https://")):
        raise ValidationError("Invalid URL format.")

    parsed = urlparse(value)

    # Scheme
    if parsed.scheme != "https":
        raise ValidationError("Only HTTPS URLs are allowed.")

    # Domain
    if parsed.netloc not in ALLOWED_HOSTS:
        raise ValidationError("Only Google Maps domains are allowed.")

    # Path must be embed
    if not parsed.path.startswith(EMBED_PATH):
        raise ValidationError("URL must be a Google Maps embed link.")

    # Required query params
    query = parse_qs(parsed.query)
    if "pb" not in query:
        raise ValidationError("Invalid embed URL (missing required parameters).")

    # Length guard
    if len(value) > 2000:
        raise ValidationError("URL is too long.")

    return value