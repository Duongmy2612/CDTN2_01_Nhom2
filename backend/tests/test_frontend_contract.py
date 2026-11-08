"""Kiểm thử tích hợp frontend – backend (sprint xây dựng 2, buổi 7): giao diện gọi đúng API của backend.

Đọc tĩnh mã React (frontend/src) và đối chiếu với hợp đồng API do FastAPI sinh ra (app.openapi()), không cần chạy
trình duyệt hay npm – nên chạy được trong CI cùng pytest. Bắt các lỗi chỉ lộ ra khi ghép hai phía:

- mỗi hàm trong src/api/client.js gọi một đường dẫn, phương thức có thật; mỗi API của backend đều có hàm gọi
- tên tham số truy vấn, trường thân yêu cầu mà giao diện gửi đều có trong API (gõ sai tên → backend bỏ qua im lặng)
- giá trị số cố định (page_size, n…) nằm trong giới hạn của API (vượt → 422)
- tên biểu đồ EDA, tên bảng CSV mà giao diện dùng đều có trong backend; bộ lọc của tab Phân tích khớp API #7, #8
- mọi hàm trong client.js đều được giao diện dùng
"""
import re
from pathlib import Path

import pytest

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "frontend" / "src"
SPEC = app.openapi()
CLIENT = (SRC / "api" / "client.js").read_text(encoding="utf-8")
FILES = {p.relative_to(SRC).as_posix(): p.read_text(encoding="utf-8") for p in SRC.rglob("*.js*") if p.name != "client.js"}


# --------------------------------------------------------------------------- #
# Đọc mã JavaScript – đủ cho cách viết của dự án (đối tượng phẳng, chuỗi '…' hoặc `…`)
# --------------------------------------------------------------------------- #
def _balanced(text: str, start: int, open_ch: str = "(", close_ch: str = ")") -> str:
    """Nội dung giữa cặp ngoặc bắt đầu tại text[start] == open_ch (bỏ qua ngoặc trong chuỗi)."""
    depth, i, quote = 0, start, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 1
            elif c == quote:
                quote = None
        elif c in "'\"`":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    raise ValueError("ngoặc không cân")


def _split_top(text: str) -> list[str]:
    parts, depth, quote, cur = [], 0, None, ""
    for i, c in enumerate(text):
        if quote:
            cur += c
            if c == quote and text[i - 1] != "\\":
                quote = None
            continue
        if c in "'\"`":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += c
    if cur.strip():
        parts.append(cur)
    return parts


def object_keys(literal: str) -> dict[str, str]:
    """{ a: 1, b, c: x || y } → {"a": "1", "b": "b", "c": "x || y"} (bỏ ...spread)."""
    body = literal.strip()
    assert body.startswith("{") and body.endswith("}"), body
    out = {}
    for part in _split_top(body[1:-1]):
        part = part.strip()
        if not part or part.startswith("..."):
            continue
        m = re.match(r"^['\"]?(\w+)['\"]?\s*(?::\s*(.*))?$", part, re.S)
        assert m, f"không đọc được khóa: {part!r}"
        out[m.group(1)] = (m.group(2) or m.group(1)).strip()
    return out


def client_functions() -> dict[str, dict]:
    """name → {method, path (mẫu FastAPI), inline (khóa tham số viết sẵn trong client), forwards (nhận params/body từ nơi gọi)}."""
    body = _balanced(CLIENT, CLIENT.index("{", CLIENT.index("export const api")), "{", "}")
    out = {}
    for part in _split_top(body):
        m = re.match(r"\s*(\w+)\s*:\s*(.*)$", part, re.S)
        if not m:
            continue
        name, code = m.groups()
        h = re.search(r"http\.(get|post|put|delete)\(\s*(['`])(.+?)\2", code)
        if h:
            method, path = h.group(1).upper(), "/api" + h.group(3)
        else:                                                  # hàm trả URL để tải file (PDF, CSV)
            u = re.search(r"(['`])(/api/.+?)\1", code)
            assert u, f"client.js: không thấy đường dẫn của hàm {name}"
            method, path = "GET", u.group(2)
        path = re.sub(r"\$\{[^}]+\}", "{x}", path)
        inline, forwards = {}, None
        pm = re.search(r"params\s*:\s*(clean\()?", code)
        if pm:
            rest = code[pm.end():].lstrip()
            if rest.startswith("{"):
                inline = object_keys("{" + _balanced(rest, 0, "{", "}") + "}")
            else:
                forwards = "query"
        if method == "POST" and re.search(r"http\.post\([^,]+,\s*body\b", code):
            forwards = "body"
        out[name] = {"method": method, "path": path, "inline": inline, "forwards": forwards,
                     "form": re.findall(r"fd\.append\(\s*'(\w+)'", code)}
    return out


def call_sites() -> list[tuple[str, str, str]]:
    """(tệp, tên hàm, đối số thứ nhất) cho mọi lời gọi api.xxx( … ) trong giao diện."""
    out = []
    for f, text in FILES.items():
        for m in re.finditer(r"\bapi\.(\w+)\(", text):
            args = _split_top(_balanced(text, m.end() - 1))
            out.append((f, m.group(1), args[0].strip() if args else ""))
    return out


FUNCS = client_functions()
SITES = call_sites()


def route_of(path: str) -> str | None:
    """Đường dẫn của client (tham số đã thay bằng {x}) → mẫu đường dẫn trong hợp đồng."""
    for p in SPEC["paths"]:
        if re.fullmatch(re.sub(r"\\\{[^}]+\\\}", r"[^/]+", re.escape(p)), path.replace("{x}", "X")):
            return p
    return None


def operation(fn: str) -> dict:
    f = FUNCS[fn]
    return SPEC["paths"][route_of(f["path"])][f["method"].lower()]


def query_params(op: dict) -> dict[str, dict]:
    return {p["name"]: p.get("schema", {}) for p in op.get("parameters", []) if p["in"] == "query"}


def path_enum(op: dict) -> set[str]:
    sch = next(p["schema"] for p in op["parameters"] if p["in"] == "path")
    return set(sch.get("enum") or [])


def body_fields(op: dict, ctype: str = "application/json") -> set[str]:
    ref = op["requestBody"]["content"][ctype]["schema"]["$ref"].split("/")[-1]
    return set(SPEC["components"]["schemas"][ref]["properties"])


def _check_number(fn: str, key: str, value: str, schema: dict):
    """Giá trị số cố định (VD page_size: 5) phải nằm trong giới hạn ge/le của API."""
    if re.fullmatch(r"\d+(\.\d+)?", value):
        v = float(value)
        lo, hi = schema.get("minimum"), schema.get("maximum")
        assert (lo is None or v >= lo) and (hi is None or v <= hi), f"api.{fn}: {key}={value} ngoài giới hạn [{lo}, {hi}] của API"


# --------------------------------------------------------------------------- #
def test_client_paths_exist_in_backend():
    for name, f in FUNCS.items():
        p = route_of(f["path"])
        assert p, f"client.js: api.{name} gọi {f['path']} – backend không có đường dẫn này"
        assert f["method"].lower() in SPEC["paths"][p], f"client.js: api.{name} dùng {f['method']} nhưng {p} không nhận phương thức này"


def test_every_backend_api_has_client_function():
    used = {(f["method"], route_of(f["path"])) for f in FUNCS.values()}
    declared = {(m.upper(), p) for p, ops in SPEC["paths"].items() for m in ops}
    assert declared - used == set(), f"API chưa có hàm gọi trong client.js: {sorted(declared - used)}"


def test_inline_query_params_exist():
    for name, f in FUNCS.items():
        allowed = query_params(operation(name))
        for k in f["inline"]:
            assert k in allowed, f"client.js: api.{name} gửi tham số '{k}' – API chỉ nhận {sorted(allowed)}"


@pytest.mark.parametrize("site", SITES, ids=lambda s: f"{s[0]}:{s[1]}")
def test_call_site_params_and_bodies(site):
    fname, fn, arg = site
    assert fn in FUNCS, f"{fname}: gọi api.{fn} – client.js không có hàm này"
    f = FUNCS[fn]
    if not arg.startswith("{") or not f["forwards"]:
        return                                                  # đối số là biến/chuỗi – kiểm ở test riêng
    keys = object_keys(arg)
    op = operation(fn)
    if f["forwards"] == "query":
        allowed = query_params(op)
        for k, v in keys.items():
            assert k in allowed, f"{fname}: api.{fn} gửi tham số '{k}' – API {f['path']} chỉ nhận {sorted(allowed)}"
            _check_number(fn, k, v, allowed[k])
    else:
        allowed = body_fields(op)
        assert set(keys) <= allowed, f"{fname}: api.{fn} gửi trường {sorted(set(keys) - allowed)} – thân yêu cầu chỉ có {sorted(allowed)}"


def test_upload_form_field():
    op = SPEC["paths"]["/api/upload"]["post"]
    assert set(FUNCS["upload"]["form"]) <= body_fields(op, "multipart/form-data")


def test_eda_chart_names():
    allowed = path_enum(operation("eda"))
    used = {re.match(r"'(\w+)'", a).group(1) for _, fn, a in SITES if fn == "eda"}
    assert used and used <= allowed, f"Tên biểu đồ không có ở API #8: {used - allowed}"


def test_eda_filters_match_api():
    """Bộ lọc của tab Phân tích (EMPTY) được gửi nguyên cho API #7 và #8 – tên phải khớp tham số của cả hai."""
    m = re.search(r"const EMPTY = (\{[^}]*\})", FILES["tabs/EdaTab.jsx"])
    keys = set(object_keys(m.group(1)))
    for fn in ("kpi", "eda"):
        allowed = set(query_params(operation(fn)))
        assert keys <= allowed, f"Bộ lọc {sorted(keys - allowed)} không có ở API {FUNCS[fn]['path']}"


def test_export_tables():
    allowed = path_enum(SPEC["paths"]["/api/export/{table}"]["get"])
    csv_block = FILES["tabs/ReportTab.jsx"].split("const CSV = [", 1)[1].split("\n]", 1)[0]
    in_report = set(re.findall(r"^\s*\['(\w+)'", csv_block, re.M))
    direct = {re.match(r"'(\w+)'", a).group(1) for _, fn, a in SITES if fn == "exportUrl" and a.startswith("'")}
    assert (in_report | direct) <= allowed, f"Bảng CSV không có ở API #20: {(in_report | direct) - allowed}"
    assert in_report == allowed, f"Tab Báo cáo chưa có nút tải: {allowed - in_report}"


def test_every_client_function_is_used():
    used = {fn for _, fn, _ in SITES}
    assert set(FUNCS) - used == set(), f"Hàm trong client.js không màn hình nào dùng: {sorted(set(FUNCS) - used)}"
