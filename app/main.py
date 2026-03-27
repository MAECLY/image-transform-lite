import sys
from pathlib import Path


def get_resource_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def main():
    import webview
    from app.config import AppConfig
    from app.api import Api

    config = AppConfig.load()
    api = Api(config)

    ui_path = get_resource_path() / "ui" / "index.html"

    window = webview.create_window(
        "Image Transform Lite",
        url=str(ui_path),
        js_api=api,
        width=800,
        height=750,
        min_size=(700, 600),
    )

    # Give the api a reference to the window for file dialogs
    api.window = window

    webview.start(debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()
