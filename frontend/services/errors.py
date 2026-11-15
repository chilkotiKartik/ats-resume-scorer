"""Turn `requests` exceptions into messages that say what happened and what to do."""

import requests


def describe_backend_error(exc: Exception) -> str:
    if isinstance(exc, requests.ConnectionError):
        return ("The scoring server isn't reachable. Start it with "
                "uvicorn backend.main:app --port 8000, or check the backend URL in secrets.toml.")
    if isinstance(exc, requests.Timeout):
        return "The scoring server took too long to answer. Try again, or try a smaller file."
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        status = exc.response.status_code
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        if status == 401:
            return "Your session has expired. Sign out and sign in again, then retry."
        if status == 422:
            return f"The file couldn't be read: {detail}"
        return f"The scoring server returned an error ({status}): {detail}"
    return f"Something went wrong: {exc}"
