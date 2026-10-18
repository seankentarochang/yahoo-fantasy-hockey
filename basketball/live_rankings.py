"""Capture the public RotoWire points cheat sheet without changing research inputs."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import urllib.request

from .backtest import digest
from .config import instant, now, path, read_json, write_json
from .ranking_library import Page, dates, validate_rows

URL = "https://www.rotowire.com/basketball/article/2026-27-fantasy-basketball-cheat-sheet-for-points-leagues-printable-excel-141449"


class Cards(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.rows, self.stack = [], []
        self.row = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        classes = set(dict(attrs).get("class", "").split())
        if "rwcs-rank-row" in classes:
            if self.row is not None:
                raise ValueError("Nested ranking cards")
            self.row = {"rank": "", "name": "", "positions": []}
        # Only div/span form this published card structure. Other markup is
        # ignored; a changed/incomplete card still fails the count/rank checks.
        if tag in {"div", "span"}:
            self.stack.append((tag, classes))

    def handle_data(self, text):
        if self.row is None or not self.stack:
            return
        classes = self.stack[-1][1]
        if "rwcs-rank-num" in classes:
            self.row["rank"] += text
        elif "rwcs-rank-player" in classes:
            self.row["name"] += text

    def handle_endtag(self, tag):
        if tag not in {"div", "span"} or not self.stack:
            return
        opened, classes = self.stack.pop()
        if opened != tag:
            raise ValueError("Ranking card markup changed")
        if "rwcs-rank-row" in classes:
            self.row["rank"] = int(self.row["rank"].strip())
            self.row["name"] = " ".join(self.row["name"].split())
            self.rows.append(self.row)
            self.row = None


def validate(cfg, root, board):
    """Use the configured live draft time, independently of research cutoffs."""
    if digest({k: v for k, v in board.items() if k != "board_sha256"}) != board.get("board_sha256"):
        raise ValueError("Selected live board changed after collection")
    spec = board["source"]
    if (spec.get("url") != URL or spec.get("season") != cfg["season"] or spec.get("family") != "RotoWire"
            or spec.get("format") != "points" or spec.get("parser") != "rotowire_cards" or spec.get("count") != 200):
        raise ValueError("Selected live ranking identity/format/coverage changed")
    raw = (root/"raw"/(spec["id"]+".html")).read_bytes()
    if hashlib.sha256(raw).hexdigest() != board["sha256"]:
        raise ValueError("Live ranking source bytes changed")
    evidence = dates(raw.decode("utf-8"))
    captured = instant(board["retrieved_at"])
    cutoff = instant(cfg["draft"]["date"])
    if (evidence != board["date_evidence"] or captured >= cutoff or captured > now(cfg)
            or any(instant(v) > captured or instant(v) >= cutoff or instant(v).year != cfg["season"]-1 for v in evidence.values())):
        raise ValueError("Live ranking dates are not verified before this draft")
    if board.get("status") != "prospective":
        raise ValueError("Live board is not a prospective preseason capture")
    validate_rows(board["rows"], spec)


def collect(cfg):
    if cfg["season"] != 2027:
        raise ValueError("This live source adapter is explicitly for 2026-27")
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.geturl() != URL:
            raise ValueError("Ranking source redirected; inspect before accepting")
        raw = response.read()
    text = raw.decode("utf-8")
    if not any("2026-27 Fantasy Basketball Cheat Sheet" in t for t in Page(text).titles):
        raise ValueError("Unexpected ranking source title")
    evidence = dates(text)
    stamp = datetime.now(timezone.utc).isoformat()
    sha = hashlib.sha256(raw).hexdigest()
    source_id = "rotowire-2027-" + evidence["dateModified"][:10].replace("-", "") + "-" + sha[:12]
    spec = {"id": source_id, "season": 2027, "family": "RotoWire", "format": "points",
            "url": URL, "parser": "rotowire_cards", "count": 200, "basis": "published standard-points expert order"}
    rows = validate_rows(Cards(text).rows, spec)
    root = path(cfg, "ranking-library")
    filename = root / "boards" / (source_id + ".json")
    board = read_json(filename)
    if board is None:
        rawfile = root / "raw" / (source_id + ".html")
        rawfile.parent.mkdir(parents=True, exist_ok=True)
        rawfile.write_bytes(raw)
        board = {"source": spec, "retrieved_at": stamp, "sha256": sha, "status": "prospective", "note": "Captured before the configured live draft time",
                 "date_evidence": evidence, "rows": rows, "full_league_projection": False}
        board["board_sha256"] = digest(board)
        write_json(filename, board)
    validate(cfg, root, board)
    selections = read_json(path(cfg, "draft-sources.json"), {})
    selections["rotowire"] = source_id
    write_json(path(cfg, "draft-sources.json"), selections)
    return {"source": source_id, "url": URL, "published_rows": len(rows), "date_evidence": evidence,
            "board_sha256": board["board_sha256"], "note": "Selected for live drafting; historical boards are unchanged"}
