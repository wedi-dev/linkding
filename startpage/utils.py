import urllib.parse


def extract_domain(url):
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        return (parsed.hostname or "").lower()
    except Exception:
        return ""


def get_registrable_domain(hostname):
    if not hostname:
        return hostname
    parts = hostname.split(".")
    if len(parts) <= 2:
        return hostname
    TWO_PART_TLDS = {
        "co.uk",
        "com.au",
        "co.nz",
        "co.jp",
        "com.pl",
        "net.pl",
        "org.pl",
        "org.uk",
        "com.br",
        "co.in",
    }
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_PART_TLDS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])
