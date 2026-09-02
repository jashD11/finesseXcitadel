"""
Point-in-time index membership, reconstructed from NSE index-review press releases.

A3 originally froze the universe as *today's* Nifty 100 + Midcap 100 constituents, on the
stated grounds that "no free 2021 membership list exists". That premise was false, and the
bias it conceded turned out to be first-order: the same 12-1 rule run on a May-2019
membership list returns +102% against +876% on today's list, and on the 2019 list momentum
*loses* to equal-weighting its own universe.

NSE publishes every index change as a dated press release at a stable URL. This module
turns those documents into a date-varying membership mask.

**The reconstruction runs backwards, and that is what makes it checkable.** Start from
today's published list, walk the changes in reverse, and at every step three invariants
must hold: each `included` name must already be present, each `excluded` name must be
absent, and the list must stay at exactly 100. A missed or misparsed release breaks one of
them immediately, so the method verifies itself rather than asking to be trusted. Measured
at the 2021-01-01 window edge: **Nifty 100 = 100, Midcap 100 = 100, union = 200,
overlap = 0.**

Three document quirks, each found by an invariant failing rather than by reading ahead:

1. The `Sr. No. Company Name Symbol` table header **repeats mid-list** wherever a table
   crosses a PDF page break, so it must be deleted everywhere rather than split on.
2. A ticker is the **last all-caps token containing a letter**. Footnote prose
   ("*Excluded on account of exclusion from Nifty Midcap 150 index") otherwise ends the
   entry on the bare number `150`, which is silently taken as the symbol.
3. Some changes are later **revoked** by a differently-formatted release, which usually
   also **substitutes** a different name in the same slot. Neither is parsed; both are
   recorded as evidence-carrying rows in the override table, in the same style A16 uses
   for corporate actions. A revocation without its substitution leaves the index at 99
   names, and the size invariant catches that immediately.

No PDF library is installed in this environment (checked), so `extract_text` inflates the
content streams with `zlib` and pulls the text-showing operands directly.
"""

from __future__ import annotations

import datetime as dt
import re
import zlib
from pathlib import Path

import pandas as pd

from src.config import Config, REPO_ROOT
from src.decisions import ConfigError

#: Section headers read "c) Nifty 100" or "9) Nifty Midcap 100".
_SECTION = re.compile(
    r'(?:^|\s)(?:[a-z]|\d{1,2})\)\s*(NIFTY\s?[A-Za-z0-9 &\-]{0,38}?)\s+The following', re.I)
_HEADER = re.compile(r'Sr\.?\s*No\.?\s*Company Name\s*Symbol', re.I)
_STOP = re.compile(r'The following|Notes?\s*:|About |The above|In order to|pursuant to', re.I)
_ENTRY = re.compile(r'\s+\d{1,3}\s+(?=[A-Z0-9])')
_TOKEN = re.compile(r'\b([A-Z0-9][A-Z0-9&\-]{1,14})\b')
_EFFECTIVE = re.compile(r'effective from ([A-Z][a-z]+ \d{1,2}, \d{4})')

#: The two indices the mandate names. Everything else in a release is ignored.
TRACKED = ("nifty 100", "nifty midcap 100")

_ESCAPES = {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b', b'f': b'\f',
            b'(': b'(', b')': b')', b'\\': b'\\'}


def _unescape(raw: bytes) -> bytes:
    out, i = bytearray(), 0
    while i < len(raw):
        ch = raw[i:i + 1]
        if ch == b'\\' and i + 1 < len(raw):
            nxt = raw[i + 1:i + 2]
            if nxt in _ESCAPES:
                out += _ESCAPES[nxt]; i += 2; continue
            if nxt.isdigit():                                   # octal escape
                j = i + 1
                while j < len(raw) and j < i + 4 and raw[j:j + 1].isdigit():
                    j += 1
                out.append(int(raw[i + 1:j], 8) & 0xFF); i = j; continue
            out += nxt; i += 2; continue
        out += ch; i += 1
    return bytes(out)


def extract_text(path: Path) -> str:
    """Inflate every content stream and concatenate the text-showing operands."""
    raw = path.read_bytes()
    chunks: list[str] = []
    for match in re.finditer(rb'stream\r?\n', raw):
        end = raw.find(b'endstream', match.end())
        if end < 0:
            continue
        try:
            data = zlib.decompress(raw[match.end():end])
        except zlib.error:
            continue
        if b'Tj' not in data and b'TJ' not in data:
            continue
        parts = []
        for op in re.finditer(rb'\((?:[^()\\]|\\.)*\)\s*(?:Tj|TJ|\')|'
                              rb'\[(?:[^\[\]\\]|\\.)*\]\s*TJ', data, re.S):
            for lit in re.finditer(rb'\((?:[^()\\]|\\.)*\)', op.group(0), re.S):
                parts.append(_unescape(lit.group(0)[1:-1]))
        chunks.append(b''.join(parts).decode('latin-1'))
    return '\n'.join(chunks)


def _normalise(name: str) -> str:
    tidy = re.sub(r'\s+', ' ', name).strip().lower().replace('nifty', 'nifty ')
    return re.sub(r'\s+', ' ', tidy).strip()


def _symbols(block: str) -> list[str]:
    block = _HEADER.sub(' ', block)                     # quirk 1: page-break headers
    out = []
    for segment in _ENTRY.split(block)[1:]:
        segment = _STOP.split(segment)[0].replace('*', ' ')
        tokens = [t for t in _TOKEN.findall(segment) if any(c.isalpha() for c in t)]
        if tokens:
            out.append(tokens[-1])                      # quirk 2: last lettered token
    return out


def parse_release(text: str, name: str) -> list[dict]:
    """Every Nifty 100 / Midcap 100 change in one press release."""
    flat = re.sub(r'\s+', ' ', text)
    effective = _EFFECTIVE.search(flat)
    if not effective:
        return []
    when = dt.datetime.strptime(effective.group(1), '%B %d, %Y').date()

    marks = [(m.start(), _normalise(m.group(1))) for m in _SECTION.finditer(flat)]
    out = []
    for i, (pos, index_name) in enumerate(marks):
        if index_name not in TRACKED:
            continue
        body = flat[pos:marks[i + 1][0] if i + 1 < len(marks) else len(flat)]
        cut_out, cut_in = body.find('being excluded'), body.find('being included')
        out.append({
            "file": name,
            "effective": when,
            "index": index_name,
            "excluded": _symbols(body[cut_out:cut_in] if 0 <= cut_in else body[cut_out:])
                        if cut_out >= 0 else [],
            "included": _symbols(body[cut_in:]) if cut_in >= 0 else [],
        })
    return out


def load_overrides(cfg: Config) -> pd.DataFrame:
    """
    Renames, revocations and cessations — evidence-carrying, like A16's table.

    A row without a source is a hard error for the same reason it is there: a membership
    change we cannot cite is a guess, and a guess in the universe is the exact defect this
    module exists to remove.
    """
    path = Path(cfg["universe.membership_overrides"])
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        raise ConfigError(f"membership override table missing: {path}")

    df = pd.read_csv(path)
    required = {"kind", "index_name", "symbol", "maps_to", "effective", "source", "note"}
    missing = required - set(df.columns)
    if missing:
        raise ConfigError(f"membership override table missing columns: {sorted(missing)}")
    unsourced = df[df["source"].isna() | (df["source"].astype(str).str.strip() == "")]
    if len(unsourced):
        raise ConfigError(
            f"membership override rows with no source: {unsourced['symbol'].tolist()}"
        )
    allowed = {"rename", "revocation", "ceased", "inclusion", "exclusion",
               "unsourced_move"}
    unknown = set(df["kind"]) - allowed
    if unknown:
        raise ConfigError(f"membership override 'kind' must be one of {sorted(allowed)}; "
                          f"got {sorted(unknown)}")
    return df


def _rename_map(overrides: pd.DataFrame) -> dict[str, str]:
    rows = overrides[overrides["kind"] == "rename"]
    return dict(zip(rows["symbol"], rows["maps_to"]))


def resolve(symbol: str, renames: dict[str, str]) -> str:
    """Follow a rename chain to the ticker the name trades under today.

    Chains are real — LTI became LTIM became LTM — so this iterates, with a seen-set so a
    bad override table loops zero times instead of forever.
    """
    seen: set[str] = set()
    while symbol in renames and symbol not in seen:
        seen.add(symbol)
        symbol = renames[symbol]
    return symbol


def changes(cfg: Config) -> list[dict]:
    """Every parsed index change, oldest first, with renames and revocations applied."""
    folder = Path(cfg["universe.press_release_dir"])
    if not folder.is_absolute():
        folder = REPO_ROOT / folder
    if not folder.is_dir():
        raise ConfigError(f"press-release snapshot missing: {folder}")

    overrides = load_overrides(cfg)
    renames = _rename_map(overrides)
    revoked = {(pd.Timestamp(r.effective).date(), r.index_name, r.symbol)
               for r in overrides[overrides["kind"] == "revocation"].itertuples()}
    # A listing that stopped existing with no successor. Suppressed from *inclusion*
    # lists only, and the asymmetry is deliberate. A ceased name that was once excluded
    # is a real constituent leaving (MINDTREE, Sept 2022) and the backward walk simply
    # adds it again -- correct, and no invariant notices. A ceased name that was once
    # included never left, so the backward walk tries to remove something today's list
    # does not contain, and the "included but absent" invariant fires. Dropping both
    # sides would silently unbalance the releases that legitimately excluded it.
    ceased = set(overrides.loc[overrides["kind"] == "ceased", "symbol"])

    records: list[dict] = []
    for pdf in sorted(folder.glob("*.pdf")):
        for rec in parse_release(extract_text(pdf), pdf.stem):
            key = (rec["effective"], rec["index"])
            rec["excluded"] = [resolve(s, renames) for s in rec["excluded"]
                               if (*key, s) not in revoked]
            rec["included"] = [resolve(s, renames) for s in rec["included"]
                               if (*key, s) not in revoked and s not in ceased]
            records.append(rec)

    # Substitutions declared in a revocation release, which `parse_release` cannot read
    # because those documents use a different table shape entirely.
    by_key = {(r["effective"], r["index"]): r for r in records}
    for row in overrides[overrides["kind"].isin(("inclusion", "exclusion"))].itertuples():
        when = pd.Timestamp(row.effective).date()
        side = "included" if row.kind == "inclusion" else "excluded"
        rec = by_key.get((when, row.index_name))
        if rec is None:
            rec = {"file": "override", "effective": when, "index": row.index_name,
                   "excluded": [], "included": []}
            by_key[(when, row.index_name)] = rec
            records.append(rec)
        rec[side].append(resolve(row.symbol, renames))

    records.sort(key=lambda r: (r["effective"], r["index"]))
    if not records:
        raise ConfigError(f"no index changes parsed from {folder}")
    return records


def roll_back(cfg: Config, today: dict[str, set[str]], as_of: dt.date,
              until: dt.date | None = None
              ) -> list[tuple[dt.date, dict[str, set[str]]]]:
    """
    Walk the changes backwards from today's published lists.

    Returns `(effective_date, membership)` pairs, oldest last, where `membership` is the
    state that held *immediately before* that date. The three invariants are asserted at
    every step -- they are the whole verification, so they are assertions and not a report.

    `until` stops the walk once the scoring window is covered, and it is a correctness
    boundary rather than an optimisation. Membership is only ever read on a rebalance
    date, the first of which is the first trading day of the window, so reconstructing
    further back buys nothing -- while the 2019-20 releases carry defects (bank mergers,
    the ALKEM/LTI reshuffle) whose repair would be pure cost. The state in force at the
    window edge is carried backwards over the lookback period, where nothing consumes it.
    """
    per_list = int(cfg["universe.expected_per_list"])
    # Names that demonstrably moved between the two indices and whose return leg is not
    # in any release we could find. The membership checks are waived for these -- by name,
    # with the search recorded in the override table -- but the size invariant is not,
    # and neither is the union: every one of them stays inside Nifty 100 + Midcap 100
    # throughout, which is the only thing eligibility reads.
    waived = set(load_overrides(cfg).pipe(
        lambda d: d.loc[d["kind"] == "unsourced_move", "symbol"]))
    current = {k: set(v) for k, v in today.items()}
    history = [(as_of, {k: set(v) for k, v in current.items()})]

    horizon = [r for r in changes(cfg) if r["effective"] <= as_of]
    if until is not None:
        # Applying the last change *inside* the window yields the state that held
        # immediately before it -- which is the state in force at `until`. Anything
        # older changes only dates nothing reads.
        horizon = [r for r in horizon if r["effective"] > until]
    for rec in sorted(horizon, key=lambda r: r["effective"], reverse=True):
        index_name, names = rec["index"], current[rec["index"]]
        absent = [s for s in rec["included"] if s not in names and s not in waived]
        present = [s for s in rec["excluded"] if s in names and s not in waived]
        assert not absent, (
            f"{rec['effective']} {index_name} ({rec['file']}): included names not in the "
            f"forward list: {absent} — a release is missing or misparsed"
        )
        assert not present, (
            f"{rec['effective']} {index_name} ({rec['file']}): excluded names still in the "
            f"forward list: {present} — a release is missing or misparsed"
        )
        current[index_name] = (names - set(rec["included"])) | set(rec["excluded"])

        # The size invariant, with the only slack it is allowed: a waived name in *this*
        # record can move the count by one, because its counterpart leg is the thing we
        # could not source. The bound is the number of waived names in this record, not a
        # constant -- a free tolerance would be exactly the fallback rule B9 refuses.
        slack = len({s for s in rec["included"] + rec["excluded"] if s in waived})
        drift = abs(len(current[index_name]) - per_list)
        assert drift <= slack, (
            f"{rec['effective']} {index_name} ({rec['file']}): rolled back to "
            f"{len(current[index_name])} names, expected {per_list} "
            f"(waived names here: {slack}) — a release is missing or misparsed"
        )
        history.append((rec["effective"], {k: set(v) for k, v in current.items()}))
    return history


def membership_spans(cfg: Config, today: dict[str, set[str]], as_of: dt.date,
                     until: dt.date | None = None) -> pd.DataFrame:
    """
    Long-format membership: one row per (index, symbol, span).

    Columns `index_name, symbol, effective_from, effective_to`, with `effective_to` empty
    for a membership that is still open at `as_of`. Written to `data/raw/` so the analysis
    path reads a file rather than re-parsing PDFs (docs/PROJECT.md §12).
    """
    history = roll_back(cfg, today, as_of, until)
    # oldest first; each entry is the state holding from that date until the next.
    ordered = list(reversed(history))
    # The oldest reconstructed state is open at its start: the walk stops once the window
    # is covered, and that state was in force for some time *before* the date it was read
    # off. Dating it to its own effective date would leave every earlier day a
    # non-member, which the B9 floor assertion catches immediately -- as it did.
    opens_at = pd.Timestamp(cfg["fetch.start"]).date()
    rows = []
    for index_name in today:
        open_from: dict[str, dt.date] = {}
        for i, (when, state) in enumerate(ordered):
            names = state[index_name]
            start = opens_at if i == 0 else when
            for symbol in names:
                open_from.setdefault(symbol, start)
            for symbol in list(open_from):
                if symbol not in names:
                    rows.append({"index_name": index_name, "symbol": symbol,
                                 "effective_from": open_from.pop(symbol),
                                 "effective_to": when})
        for symbol, start in open_from.items():
            rows.append({"index_name": index_name, "symbol": symbol,
                         "effective_from": start, "effective_to": pd.NaT})
    out = pd.DataFrame(rows).sort_values(["index_name", "symbol", "effective_from"])
    return out.reset_index(drop=True)


def matrix(spans: pd.DataFrame, symbols: pd.Series, days: pd.DatetimeIndex) -> pd.DataFrame:
    """
    (date x isin) boolean membership: True where the name was in *either* index that day.

    The union is what the mandate names and what eligibility needs, so which of the two
    indices a name sits in never reaches the strategy. That matters: several names swap
    between Nifty 100 and Midcap 100 mid-window, and the union is unaffected by the swap.
    """
    by_symbol = {v: k for k, v in symbols.items()}
    out = pd.DataFrame(False, index=days, columns=list(symbols.index))
    for row in spans.itertuples():
        isin = by_symbol.get(row.symbol)
        if isin is None:
            continue
        start = pd.Timestamp(row.effective_from)
        stop = pd.Timestamp(row.effective_to) if pd.notna(row.effective_to) else None
        window = (days >= start) if stop is None else ((days >= start) & (days < stop))
        out.loc[window, isin] = True
    return out
