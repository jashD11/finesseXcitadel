"""
Network layer. Runs once, writes ``data/raw/``, and is never imported by anything
that computes a return.

Two hard rules, both structural rather than advisory:

- **Nothing here is called from the backtest.** ``scripts/01_fetch.py`` is the only
  entry point, and the file system is the boundary between this module and analysis.
- **Snapshots are immutable.** Yahoo restates history, so a run pinned to an ``as_of``
  stamp is the only way a result is reproducible. ``write_snapshot`` refuses to
  overwrite; re-running is a no-op, not a refresh.

Nothing in this module cleans, fills, aligns or adjusts anything. What Yahoo and NSE
return is what lands on disk, so the cleaning rules (A9-A12, still open) are applied
downstream where they can be seen and tested.
"""

from __future__ import annotations

import io
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
import yfinance as yf

from src.config import Config
from src.decisions import ConfigError

_OHLCV = ["open", "high", "low", "close", "adj_close", "volume"]
_ACTIONS = ["dividends", "split"]

_COLUMN_MAP = {
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "adj_close",
    "volume": "volume",
    "dividends": "dividends",
    "stock splits": "split",
}


# ── Universe ─────────────────────────────────────────────────────────────────


def _get_csv(url: str, user_agent: str, retries: int, pause: float) -> pd.DataFrame:
    """NSE serves these only to a browser User-Agent; a plain client gets nothing."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
            resp.raise_for_status()
            body = resp.content
            if body[:1] == b"<":
                raise RuntimeError(f"{url} returned HTML, not CSV (decoy or error page)")
            return pd.read_csv(io.BytesIO(body))
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised below
            last = exc
            time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url} after {retries} attempts: {last}")


def fetch_universe(cfg: Config) -> pd.DataFrame:
    """
    Both NSE constituent lists, as one frame.

    A3 (frozen) fixes the snapshot to today's lists. ``Industry`` is retained because
    backlog item 5 (sector cap) needs it and it is not available anywhere else.
    """
    ua = cfg["fetch.user_agent"]
    retries = cfg["fetch.max_retries"]
    pause = cfg["fetch.request_pause_s"]
    per_list = cfg["universe.expected_per_list"]

    frames = []
    for index_name, key in (("NIFTY100", "universe.nifty100_url"),
                            ("MIDCAP100", "universe.midcap100_url")):
        raw = _get_csv(cfg[key], ua, retries, pause)
        raw.columns = [c.strip() for c in raw.columns]
        df = pd.DataFrame({
            "index_name": index_name,
            "company_name": raw["Company Name"].str.strip(),
            "industry": raw["Industry"].str.strip(),
            "symbol": raw["Symbol"].str.strip(),
            "series": raw["Series"].str.strip(),
            "isin": raw["ISIN Code"].str.strip(),
        })
        assert len(df) == per_list, f"{index_name}: expected {per_list} rows, got {len(df)}"
        frames.append(df)

    uni = pd.concat(frames, ignore_index=True)
    uni["yahoo_symbol"] = uni["symbol"] + cfg["universe.yahoo_suffix"]

    total = cfg["universe.expected_total"]
    assert len(uni) == total, f"expected {total} rows, got {len(uni)}"
    # A4 verified the two lists are disjoint. Asserted rather than trusted, because a
    # future index reshuffle could overlap them and silently shrink the universe.
    assert uni["symbol"].nunique() == total, "duplicate symbols across the two lists"
    assert uni["isin"].nunique() == total, "duplicate ISINs across the two lists"
    return uni.sort_values("symbol").reset_index(drop=True)


# ── Prices ───────────────────────────────────────────────────────────────────


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.rename(columns={c: _COLUMN_MAP.get(str(c).strip().lower(), str(c))
                                  for c in frame.columns})
    for col in _OHLCV + _ACTIONS:
        if col not in frame.columns:
            frame[col] = pd.NA
    return frame


def _download(tickers: list[str], start: str, end: str, retries: int,
              pause: float) -> pd.DataFrame:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            raw = yf.download(
                tickers=tickers,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,   # A2 needs raw Close; Adj Close stored but unused
                actions=True,
                group_by="ticker",
                progress=False,
                threads=True,
            )
            if raw is not None and len(raw):
                return raw
            last = RuntimeError("empty frame")
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised below
            last = exc
        time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"download failed for {len(tickers)} tickers: {last}")


def fetch_prices(cfg: Config, yahoo_symbols: list[str]) -> pd.DataFrame:
    """
    Daily OHLCV plus ``Adj Close``, dividends and splits, in long format.

    Returned as-is: no alignment to a common calendar, no filling, no adjustment.
    Those are cleaning decisions and they belong in ``clean.py``.
    """
    start = str(cfg["fetch.start"])
    end = _end_date(cfg)
    batch = cfg["fetch.batch_size"]
    pause = cfg["fetch.request_pause_s"]
    retries = cfg["fetch.max_retries"]

    out: list[pd.DataFrame] = []
    for i in range(0, len(yahoo_symbols), batch):
        chunk = yahoo_symbols[i:i + batch]
        raw = _download(chunk, start, end, retries, pause)
        present = set(raw.columns.get_level_values(0)) if isinstance(
            raw.columns, pd.MultiIndex) else set(chunk)
        for ticker in chunk:
            if ticker not in present:
                continue
            sub = raw[ticker] if isinstance(raw.columns, pd.MultiIndex) else raw
            sub = _normalise(sub.copy()).reset_index()
            sub = sub.rename(columns={"Date": "date", "index": "date"})
            sub["yahoo_symbol"] = ticker
            sub = sub.dropna(subset=["close"])
            if len(sub):
                out.append(sub[["date", "yahoo_symbol"] + _OHLCV + _ACTIONS])
        time.sleep(pause)

    if not out:
        raise RuntimeError("no price data returned for any symbol")
    prices = pd.concat(out, ignore_index=True)
    prices["date"] = pd.to_datetime(prices["date"]).dt.tz_localize(None).dt.normalize()
    return prices.sort_values(["yahoo_symbol", "date"]).reset_index(drop=True)


def fetch_indices(cfg: Config) -> pd.DataFrame:
    """
    Benchmark index series. ``NIFTY_MIDCAP_100.NS`` is deliberately not fetched:
    measured at 1,610 observations against 1,643 for ``^NSEI``, last print five weeks
    stale. A Midcap benchmark, if D1 calls for one, gets built from constituents.
    """
    return fetch_prices(cfg, list(cfg["fetch.indices"]))


def _end_date(cfg: Config) -> str:
    """yfinance treats ``end`` as exclusive, so the run date needs one day added."""
    raw = cfg.raw("fetch.end")
    stop = date.today() if raw is None else pd.Timestamp(raw).date()
    return (stop + timedelta(days=1)).isoformat()


# ── Immutable snapshots ──────────────────────────────────────────────────────


def write_snapshot(df: pd.DataFrame, path: Path, as_of: str, source: str,
                   extra: dict[str, str] | None = None) -> None:
    """
    Write a parquet pinned with an ``as_of`` stamp, refusing to overwrite.

    The refusal is the point (A14). Yahoo restates history, so silently replacing a
    snapshot would change every result computed from it with no trace.
    """
    if path.exists():
        raise FileExistsError(
            f"{path} exists. Snapshots are immutable (A14) — delete it deliberately "
            f"if you really mean to re-fetch."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    meta: dict[bytes, bytes] = dict(table.schema.metadata or {})
    meta[b"as_of"] = as_of.encode()
    meta[b"source"] = source.encode()
    meta[b"rows"] = str(len(df)).encode()
    for key, value in (extra or {}).items():
        meta[key.encode()] = str(value).encode()
    pq.write_table(table.replace_schema_metadata(meta), path)


def read_snapshot(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load a snapshot and assert its provenance stamp survived the round trip."""
    table = pq.read_table(path)
    meta = {k.decode(): v.decode() for k, v in (table.schema.metadata or {}).items()
            if not k.startswith(b"pandas")}
    if "as_of" not in meta:
        raise ConfigError(f"{path} has no as_of stamp — not a pinned snapshot")
    return table.to_pandas(), meta


def snapshot_path(cfg: Config, kind: str, as_of: str) -> Path:
    stamp = as_of.replace("-", "")
    suffix = "csv" if kind == "universe" else "parquet"
    return cfg.resolved_path("paths.data_raw") / f"{kind}_{stamp}.{suffix}"


def today_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")
