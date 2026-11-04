"""PLAN-058 targeted theme-adoption probe for 020-music-player.

Counter-controls (auto-os/PLAN-058 V-01/V-02 standalone legs), two boots:

  leg A (explicit override track): AUTO_UI_THEME=dark -> official Auto/dark
      applied: interior pixel == #09090b (vendor/themes Auto family dark
      background), dark_mode state true
  leg B (OS-follow track): AUTO_UI_THEME unset -> OS system theme seeds
      dark_mode (PLAN-615 T-04 chain: CLI > os-config > pac.at > system);
      on a light-OS machine this boots light -> interior pixel #ffffff

Business sentinels (both legs): real scan of the managed fixture root
(3 tracks, playlist, playing state) -- theme round-trip must not lose the
active business state (V-02).

Original gate tests/test_020_vm.py stays untouched. Fixture data lives in
D:/autostack/plan-artifacts/plan-058/auto-os/fixtures/music-root (never the
user's real music library).
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

FIXTURE_ROOT = r"D:\autostack\plan-artifacts\plan-058\auto-os\fixtures\music-root"
EVIDENCE_DIR = r"D:\autostack\plan-artifacts\plan-058\auto-os\music"
EXPECTED_TRACKS = 3

# Official Auto family (vendor/themes/themes.at, digest 9fa07742..bef838e)
AUTO_DARK_BG = (0x09, 0x09, 0x0B)
AUTO_LIGHT_BG = (0xFF, 0xFF, 0xFF)


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class AutoUiMcpClient:
    def __init__(self, port: int):
        self.url = f"http://127.0.0.1:{port}/mcp"
        self._req_id = 1

    def call(self, tool_name: str, args: dict = None) -> dict:
        req = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args or {}},
        }
        self._req_id += 1
        data = json.dumps(req).encode("utf-8")
        http_req = urllib.request.Request(
            self.url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(http_req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "error" in res:
                raise RuntimeError(f"MCP Tool '{tool_name}' error: {res['error']}")
            return res.get("result", {})

    def text(self, tool_name: str, args: dict = None) -> str:
        return self.call(tool_name, args).get("content", [{}])[0].get("text", "")

    def state(self) -> str:
        return self.text("autoui_state")

    def screenshot(self, name: str) -> str:
        raw = self.text("autoui_screenshot", {"name": name, "baseline": False})
        low = raw.lower()
        if "saved to" in low:
            after = raw[low.index("saved to") + len("saved to"):].lstrip(" :").replace("\\\\?\\", "")
            return after.strip()
        return ""

    def list_tools(self) -> list:
        req = {"jsonrpc": "2.0", "id": self._req_id, "method": "tools/list", "params": {}}
        self._req_id += 1
        data = json.dumps(req).encode("utf-8")
        http_req = urllib.request.Request(
            self.url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(http_req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
        return [t.get("name") for t in res.get("result", {}).get("tools", [])]


def interior_pixel(png_path: str):
    """Average a main-area 6x6 patch (right of the 240px sidebar, off the
    window edge): the root bg-background surface, expected to equal the
    official package token exactly."""
    from PIL import Image

    with Image.open(png_path) as im:
        rgb = im.convert("RGB")
        px = [rgb.getpixel((x, y)) for x in range(700, 706) for y in range(24, 30)]
    n = len(px)
    return tuple(round(sum(c[i] for c in px) / n) for i in range(3))


def boot_once(app_dir: str, auto_bin: str, env_extra: dict, shot_name: str, failures: list) -> None:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    port = pick_free_port()
    env = dict(os.environ, AUTOUI_MCP_PORT=str(port), AUTO_MEDIA_ROOT=FIXTURE_ROOT, **env_extra)
    proc = subprocess.Popen([auto_bin, "run", "-r", "vm"], cwd=app_dir, env=env)
    try:
        client = AutoUiMcpClient(port)
        start = time.time()
        state = ""
        while time.time() - start < 420:
            try:
                s = client.state()
                if "item_count" in s:
                    state = s
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not state:
            failures.append(f"{shot_name}: MCP not ready within 420s")
            return
        time.sleep(3)  # settle: scan render + theme publish

        # business sentinels (V-02): real scan of managed fixture
        checks = [
            (f"item_count: {EXPECTED_TRACKS}", "scan parsed 3 tracks"),
            ("__scan_ok: true", "scan ok flag"),
            ("has_current: true", "current track loaded"),
            ("is_playing: true", "playing state active"),
        ]
        for needle, why in checks:
            if needle in state:
                print(f"  [+] state ok: {why}")
            else:
                failures.append(f"{shot_name}: state sentinel missing: {needle}")

        # theme leg pixel oracle (V-01)
        tmp = client.screenshot(shot_name)
        if tmp and os.path.exists(tmp):
            shot = os.path.join(EVIDENCE_DIR, f"{shot_name}.png")
            with open(tmp, "rb") as s, open(shot, "wb") as d:
                d.write(s.read())
            r, g, b = interior_pixel(shot)
            expected = AUTO_DARK_BG if "dark" in shot_name else AUTO_LIGHT_BG
            print(f"  [*] interior pixel = #{r:02x}{g:02x}{b:02x} (expect #{expected[0]:02x}{expected[1]:02x}{expected[2]:02x})")
            if all(abs(a - c) <= 3 for a, c in zip((r, g, b), expected)):
                print(f"  [+] {shot_name}: official package value applied")
            else:
                failures.append(f"{shot_name}: interior pixel #{r:02x}{g:02x}{b:02x} != expected #{'%02x%02x%02x' % expected}")
        else:
            failures.append(f"{shot_name}: screenshot not saved")

        dm = [l.strip() for l in state.splitlines() if "dark_mode" in l]
        print(f"  [*] dark_mode state: {dm}")
        if "dark" in shot_name and "dark_mode: true" not in state:
            failures.append(f"{shot_name}: dark_mode state not true")

        with open(os.path.join(EVIDENCE_DIR, f"state-{shot_name}.json"), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        tmp_dir = os.path.join(app_dir, "src", "front", "tmp")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    failures: list = []
    if not os.path.isdir(FIXTURE_ROOT):
        print("[-] fixture root missing")
        return 2

    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auto_bin = os.environ.get("AUTO_BIN", "auto")

    print(f"[*] leg A: explicit AUTO_UI_THEME=dark (override track)")
    boot_once(app_dir, auto_bin, {"AUTO_UI_THEME": "dark"}, "058_music_dark", failures)

    print(f"[*] leg B: AUTO_UI_THEME unset (OS-follow track)")
    boot_once(app_dir, auto_bin, {}, "058_music_osfollow", failures)

    # MCP tool surface inventory (one boot, hosted-probe inputs)
    port = pick_free_port()
    env = dict(os.environ, AUTOUI_MCP_PORT=str(port), AUTO_MEDIA_ROOT=FIXTURE_ROOT, AUTO_UI_THEME="dark")
    proc = subprocess.Popen([auto_bin, "run", "-r", "vm"], cwd=app_dir, env=env)
    try:
        client = AutoUiMcpClient(port)
        start = time.time()
        while time.time() - start < 120:
            try:
                s = client.state()
                if "item_count" in s:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        tools = client.list_tools()
        print(f"[*] MCP tools: {tools}")
        with open(os.path.join(EVIDENCE_DIR, "mcp-tools.json"), "w", encoding="utf-8") as f:
            json.dump(tools, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print(f"[!] tools/list failed (non-fatal): {e}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        tmp_dir = os.path.join(app_dir, "src", "front", "tmp")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

    if failures:
        print("[-] FAILURES:")
        for f in failures:
            print("   -", f)
        return 1
    print("[+] PLAN-058 music probe: all counter-controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
