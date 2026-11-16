"""Drive remote ka Google login, kisi bhi khaali loopback port par.

Kyon: rclone apna login hamesha 127.0.0.1:53682 par karta hai. Kuch Windows machines par yeh port
"excluded port range" mein aa jaata hai (Hyper-V/WSL/Docker), aur rclone ka login chal hi nahin paata.
Yeh script wahi OAuth login (Desktop client, PKCE) ek khaali port par karti hai aur token ko rclone
config ke usi remote mein likh deti hai. Scope sirf drive.file.

    python tools/setup/drive_login.py --remote granth --ask-client          (naya client: ID aur secret poochhta hai)
    python tools/setup/drive_login.py --remote granth --reuse-from <remote>  (kisi purane remote ka client)

- --ask-client: client ID aur secret terminal mein poochhe jaate hain (secret dikhta nahin). Agar remote pehle se
  kisi doosre client ke saath bana hai, to uska client aur token naye se badal diye jaate hain.
- --reuse-from: client ID/secret purane remote se sirf memory mein padhe jaate hain. Koi maan chhapta nahin.
- rclone config mein sirf [--remote] wala section badalta hai (ek 'token = ...' line). Baaki file jaisi thi.
- Token sirf is laptop ke rclone config mein rehta hai: na repo mein, na chat mein.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import hashlib
import http.server
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser

SCOPE = "https://www.googleapis.com/auth/drive.file"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def rclone(*args: str) -> str:
    return subprocess.run(["rclone", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def client_of(remote: str) -> tuple[str, str]:
    cid = sec = ""
    for line in rclone("config", "show", remote).splitlines():
        m = re.match(r"^(client_id|client_secret)\s*=\s*(\S+)", line)
        if m:
            if m.group(1) == "client_id":
                cid = m.group(2)
            else:
                sec = m.group(2)
    if not cid.endswith(".apps.googleusercontent.com") or not sec:
        sys.exit(f"Remote '{remote}' mein apna OAuth client nahin mila.")
    return cid, sec


def wait_for_code(port: int, state: str) -> str:
    got: dict[str, str] = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "state" in q or "error" in q:
                got.update({k: v[0] for k, v in q.items()})
                ok = q.get("state", [""])[0] == state and "code" in q
                body = "Login ho gaya. Yeh tab band kar sakte hain." if ok else "Login poora nahin hua. Terminal dekhein."
            else:
                body = "..."
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a: object) -> None:  # request line (code ke saath) kahin na chhape
            pass

    srv = http.server.HTTPServer(("127.0.0.1", port), H)
    srv.timeout = 5
    deadline = dt.datetime.now() + dt.timedelta(minutes=5)
    while not got and dt.datetime.now() < deadline:
        srv.handle_request()
    srv.server_close()
    if not got:
        sys.exit("5 minute mein login nahin hua; dobara chalao.")
    if got.get("error"):
        sys.exit("Google ne mana kiya: " + got["error"])
    if got.get("state") != state or "code" not in got:
        sys.exit("Galat jawab mila (state mel nahin khaata); dobara chalao.")
    return got["code"]


def write_token(remote: str, token_json: str) -> None:
    path = rclone("config", "file").strip().splitlines()[-1].strip()
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == f"[{remote}]")
    except StopIteration:
        sys.exit(f"rclone config mein [{remote}] nahin mila.")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    body = [l for l in lines[start + 1:end] if not re.match(r"^token\s*=", l)]
    while body and body[-1].strip() == "":
        body.pop()
    body.append("token = " + token_json)
    body.append("")
    out = nl.join(lines[:start + 1] + body + lines[end:])
    tmp = path + ".tmp-drive-login"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", default="granth")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--reuse-from", help="woh rclone remote jiska OAuth client dobara istemal ho")
    g.add_argument("--ask-client", action="store_true", help="client ID aur secret terminal mein poochho")
    a = ap.parse_args()

    remotes = rclone("listremotes").split()
    if a.ask_client:
        cid = input("Client ID chipkao (....apps.googleusercontent.com): ").strip()
        sec = getpass.getpass("Client secret chipkao (dikhega nahin), phir Enter: ").strip()
        if not cid.endswith(".apps.googleusercontent.com") or not sec:
            sys.exit("Client ID ya secret sahi nahin dikhta; ruk rahe hain.")
        if f"{a.remote}:" in remotes:
            # purane client ka token naye client ke saath nahin chalega: section ko naye client par le aao
            subprocess.run(["rclone", "config", "delete", a.remote], check=True, capture_output=True)
            remotes = rclone("listremotes").split()
    else:
        if f"{a.reuse_from}:" not in remotes:
            sys.exit(f"Remote '{a.reuse_from}' nahin mila.")
        cid, sec = client_of(a.reuse_from)
    if f"{a.remote}:" not in remotes:
        subprocess.run(["rclone", "config", "create", a.remote, "drive", "scope=drive.file", f"client_id={cid}",
                        f"client_secret={sec}", "config_is_local=false", "--non-interactive", "--no-output"],
                       check=False, capture_output=True)
        if f"{a.remote}:" not in rclone("listremotes").split():
            sys.exit(f"Remote '{a.remote}' nahin ban saka.")
    shown = rclone("config", "show", a.remote)
    if not re.search(r"^scope\s*=\s*drive\.file\s*$", shown, re.M):
        sys.exit(f"Remote '{a.remote}' ka scope drive.file nahin hai; ruk rahe hain.")

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    redirect = f"http://127.0.0.1:{port}/"
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    print(f"Browser mein Google login khul raha hai (port {port}). Apna khaata chuno aur 'Allow' / 'Continue' dabao...")
    if not webbrowser.open(url):
        print("Browser apne-aap nahin khula. Script dobara chalao, ya default browser set karo.")
    code = wait_for_code(port, state)

    req = urllib.request.Request(TOKEN_URL, data=urllib.parse.urlencode({
        "code": code, "client_id": cid, "client_secret": sec, "redirect_uri": redirect,
        "grant_type": "authorization_code", "code_verifier": verifier,
    }).encode(), headers={"content-type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            tok = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Token nahin mila: HTTP {e.code}")
    if "refresh_token" not in tok:
        sys.exit("Google ne refresh token nahin diya; dobara chalao.")
    if SCOPE not in tok.get("scope", "").split():
        sys.exit("Mila hua scope drive.file nahin hai; ruk rahe hain.")
    expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=int(tok.get("expires_in", 3600)))).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    write_token(a.remote, json.dumps({"access_token": tok["access_token"], "token_type": "Bearer",
                                      "refresh_token": tok["refresh_token"], "expiry": expiry}, separators=(",", ":")))
    print(f"Login ho gaya. Remote '{a.remote}' taiyaar hai (scope: drive.file).")


if __name__ == "__main__":
    main()
