from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from megafon_desktop import __version__
from megafon_desktop.infra.db import Database
from megafon_desktop.infra.paths import database_path
from megafon_desktop.infra.secret_store import WindowsDpapiSecretStore
from megafon_desktop.megafon.http_transport import DirectHttpTransport
from megafon_desktop.services.account_service import AccountService
from megafon_desktop.ui.icon import make_app_icon
from megafon_desktop.ui.main_window import MainWindow


def build_service() -> AccountService:
    db = Database(database_path())
    secrets = WindowsDpapiSecretStore()
    transport = DirectHttpTransport(secrets=secrets)
    return AccountService(db, secrets, transport)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Megafon Desktop")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(make_app_icon())
    window = MainWindow(build_service())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
