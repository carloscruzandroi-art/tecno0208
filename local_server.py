from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sqlite3
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent
DB = ROOT / "tecnozona.db"
HOST = "127.0.0.1"
PORT = 8765
MAX_BODY = 25 * 1024 * 1024


def connect():
    conn = sqlite3.connect(DB, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    return conn


def valid_state(state):
    return (isinstance(state, dict)
            and isinstance(state.get("clients"), list)
            and isinstance(state.get("orders"), list)
            and isinstance(state.get("staff"), list)
            and isinstance(state.get("company"), dict))


class Handler(BaseHTTPRequestHandler):
    server_version = "TecnoZonaLocal/1.0"

    def respond(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/ping":
            return self.respond(200, {"ok": True, "database": "SQLite local"})
        if path == "/api/state":
            try:
                with connect() as conn:
                    row = conn.execute("SELECT payload FROM app_state WHERE id=1").fetchone()
                return self.respond(200, {"ok": True, "state": json.loads(row[0]) if row else None})
            except Exception as exc:
                return self.respond(500, {"ok": False, "error": str(exc)})
        if path in ("/", "/index.html"):
            self.path = "/index.html"
            return super().do_GET()
        return self.respond(404, {"ok": False, "error": "No encontrado"})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/state":
            return self.respond(404, {"ok": False, "error": "No encontrado"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400, {"ok": False, "error": "Tamaño inválido"})
        if length < 2 or length > MAX_BODY:
            return self.respond(413, {"ok": False, "error": "El respaldo excede el límite de 25 MB"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not valid_state(body):
                return self.respond(400, {"ok": False, "error": "Estructura de datos inválida"})
            payload = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
            with connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute("SELECT payload FROM app_state WHERE id=1").fetchone()
                if row:
                    conn.execute("INSERT INTO backups(payload) VALUES (?)", (row[0],))
                    conn.execute("DELETE FROM backups WHERE id NOT IN (SELECT id FROM backups ORDER BY id DESC LIMIT 20)")
                conn.execute("INSERT INTO app_state(id,payload,updated_at) VALUES (1,?,CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP", (payload,))
                conn.commit()
            return self.respond(200, {"ok": True})
        except json.JSONDecodeError:
            return self.respond(400, {"ok": False, "error": "JSON inválido"})
        except Exception as exc:
            return self.respond(500, {"ok": False, "error": str(exc)})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    with connect() as conn:
        conn.commit()
    server = ThreadingHTTPServer((HOST, PORT), lambda *args, **kwargs: Handler(*args, directory=str(ROOT), **kwargs))
    print("TecnoZona está lista en http://%s:%s" % (HOST, PORT))
    print("Base local: %s" % DB)
    print("No cierres esta ventana mientras uses el sistema. Ctrl+C para detenerlo.")
    threading.Timer(1.0, lambda: webbrowser.open("http://%s:%s/" % (HOST, PORT))).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor local detenido.")
    finally:
        server.server_close()
