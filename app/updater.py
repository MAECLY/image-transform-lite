import json
import urllib.request

GITHUB_API_URL = "https://api.github.com/repos/miguel50flowers/fe-image-transform-lite/releases/latest"
TIMEOUT_SECONDS = 5


def compare_versions(current: str, latest: str) -> bool:
    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    try:
        return parse(latest) > parse(current)
    except (ValueError, AttributeError):
        return False


def check_for_updates(current_version: str) -> dict:
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ImageTransformLite",
            },
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")

        if not compare_versions(current_version, latest):
            return {"update_available": False}

        download_url = data.get("html_url", "")
        for asset in data.get("assets", []):
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        return {
            "update_available": True,
            "latest_version": latest,
            "current_version": current_version,
            "download_url": download_url,
            "release_url": data.get("html_url", ""),
        }
    except Exception:
        return {"update_available": False}
