from datetime import datetime, timezone, time
from fastapi import HTTPException

def parse_iso_to_datetime(value: str | datetime) -> datetime:
    """
    Parse ISO8601-like string or datetime to a datetime object.
    Accepts:
      - "2026-06-23T13:31:18.665Z"
      - "2026-06-23T13:31:18+03:00"
      - "2026-06-23 13:31:18"
      - datetime instances (returned as-is)
    Raises HTTPException(400) on invalid input.
    """
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"Invalid datetime type: {type(value).__name__}")

    s = value.strip()
    # Normalize trailing Z to +00:00 for fromisoformat
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    # Try fromisoformat (handles offsets)
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass

    # Fallback formats
    fmts = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise HTTPException(status_code=400, detail=f"Invalid datetime format: {value}")


def _ensure_precision(s: str, precision: int) -> str:
    """
    Helper: ensure string has fractional part with requested precision.
    Accepts "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DDTHH:MM:SS(.fff...)".
    """
    s = s.replace("T", " ").strip()
    if "." not in s:
        frac = "0" * precision
        return f"{s}.{frac}"
    base, frac = s.split(".", 1)
    frac = ''.join(ch for ch in frac if ch.isdigit())
    if len(frac) >= precision:
        return f"{base}.{frac[:precision]}"
    return f"{base}.{frac.ljust(precision, '0')}"


def format_for_ch_datetime(dt: datetime | str, precision: int = 0, to_utc: bool = False) -> str:
    """
    Format datetime or string for ClickHouse DateTime / DateTime64.
    - precision: 0 -> "YYYY-MM-DD HH:MM:SS"
                 1..6 -> "YYYY-MM-DD HH:MM:SS.fff..." (DateTime64)
    - to_utc: if True and dt has tzinfo, convert to UTC before formatting.

    Returns string like:
      "2026-06-23 13:31:18"
      "2026-06-23 13:31:18.665"  (precision=3)
    """
    if isinstance(dt, str):
        s = dt.strip()
        if s.endswith("Z"):
            s = s[:-1].replace("T", " ")
        return s if precision == 0 else _ensure_precision(s, precision)

    if not isinstance(dt, datetime):
        raise TypeError("dt must be datetime or ISO string")

    if to_utc:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)

    if precision <= 0:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    micros = dt.microsecond  # 0..999999
    frac = f"{micros:06d}"[:precision]
    base = dt.strftime("%Y-%m-%d %H:%M:%S")
    return f"{base}.{frac}"


def format_for_ch_date(dt: datetime) -> str:
    """Return YYYY-MM-DD for ClickHouse Date parameters."""
    if not isinstance(dt, datetime):
        raise TypeError("dt must be datetime")
    return dt.date().isoformat()


def get_default_from_date() -> datetime:
    """Default from_date: 30 days ago."""
    return datetime.now() - timedelta(days=30)


def normalize_to_date(d: datetime | None) -> datetime:
    """
    If time is midnight, normalize to 23:59:59 of that day; keep datetime otherwise.
    If d is None, return now().
    """
    if d is None:
        return datetime.now()
    if d.time() == time(0, 0, 0):
        return datetime.combine(d.date(), time(23, 59, 59))
    return d
