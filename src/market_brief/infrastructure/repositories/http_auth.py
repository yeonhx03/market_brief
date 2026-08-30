WRITE_API_KEY_HEADER = "X-Market-Brief-Key"


def build_write_headers(api_key: str | None) -> dict[str, str]:
    if api_key is None or api_key.isspace():
        return {}

    return {WRITE_API_KEY_HEADER: api_key}
