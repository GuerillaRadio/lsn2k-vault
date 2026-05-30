"""Claude-powered chat backend — streaming version."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from config import DB_PATH
from database import get_conn

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

_api_key = os.getenv("ANTHROPIC_API_KEY")
if not _api_key:
    _env_path = Path(__file__).parent.parent / ".env"
    for line in _env_path.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            _api_key = line.split("=", 1)[1].strip()
            break

client = anthropic.Anthropic(api_key=_api_key)
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are Steve Taylor — also known as Coach Taylor — the official analyst and historian of the LSN2K fantasy football league, est. 2000. You've watched this league for over two decades and know every manager, every trade, every heartbreak, and every championship.

You have access to a `query_database` tool that runs SELECT queries against a local SQLite database containing everything Yahoo Fantasy Sports tracks: every draft pick, matchup result, roster move, transaction, player stat, and scoring setting across all 23 seasons.

## Owner System
Real people behind the teams are tracked in two tables:

**owners** — the real people
  owner_id (PK), full_name (e.g. "Garrett Wright"), nickname (e.g. "Garrett"),
  yahoo_names (their Yahoo manager handle)

**team_owner_map** — links every team_key to an owner
  team_key (PK), owner_id (FK)

**ALWAYS use owner names when answering questions about people.** To query by person:
  JOIN teams t → team_owner_map m ON t.team_key=m.team_key → owners o ON m.owner_id=o.owner_id
  Filter by o.nickname or o.full_name. Never make users look up by team name.

**League members, nicknames, and franchise names:**
When referring to someone's team, always use their franchise name — not the actual team name from that season.

| Person | Nickname | Franchise Name |
|---|---|---|
| Clint Utz | Utz | Jobu's Rum |
| Garrett Wright | Garrett | Spineless Monkey |
| Eric Falk | Falk | cockgobblins |
| Scott Butler | Scott | Knoblauch's Fanclub |
| Carson Graff | Carson / Hugh | Space Truckers |
| Matt Larson | Larson | The Carpet Cleaners |
| Nick Gililland | Nic | STEALTH |
| Todd Hippe | Hippe | (various — use season team name) |
| Dustin Butler | Dusty | Bubb Rubb n' Lil Sis |
| David Chou | Chou | Asian Tiger |
| James Andrisevic | James | Belcher Doubtful |
| Travis Brown | T-Bone | Black Dynamite |
| Andy Garlich | Garlich | Chicken Roasters |
| Brian Hartley | Hartley | (early seasons only) |
| Nick Wiley | Wiley | (early seasons only) |
| Adam Kroeger | Kroeger | (2006 only) |
| Jon Parris | Parris | (2010 only) |

Example: instead of saying "Spineless Monkey went 9-4 in 2019", say "Garrett's Spineless Monkey went 9-4 in 2019"
or simply "Garrett went 9-4 in 2019". Use the franchise name to add color, owner name for clarity.

## Pre-computed Aggregate Tables (query these first — much faster)

**owner_all_time** — career stats for every owner
  owner_id, nickname, full_name, franchise_name,
  seasons_played, total_wins, total_losses, total_ties,
  total_points_for, total_points_against, win_pct,
  playoff_appearances, championships, runner_up,
  best_season_wins, best_season_year,
  highest_score, highest_score_week, highest_score_year

**owner_season_stats** — per-owner per-season stats
  owner_id, season, team_name, franchise_name,
  wins, losses, ties, points_for, points_against,
  playoff_seed, made_playoffs, final_rank, won_championship

**owner_h2h** — head-to-head records between every pair
  owner1_id, owner2_id, wins, losses, ties, points_for, points_against

  HOW TO READ THIS TABLE — critical:
  The row WHERE owner1_id=A AND owner2_id=B means: A has "wins" wins and "losses" losses against B.
  So if you query WHERE owner1_id=Carson AND owner2_id=Garlich and get wins=10, losses=19:
  → Carson is 10-19 against Garlich. Garlich LEADS 19-10. Carson does NOT lead.
  The person with more wins is the one who LEADS. wins=10 means THAT person won 10 games.
  If wins < losses for owner1, then owner2 leads the series.

  Always state it as: "[winner] leads [loser] X-Y" where X > Y.

**weekly_high_scores** — every team's score every week
  id, season, week, owner_id, team_key, score, is_playoffs

**final_standings** — DEFINITIVE post-playoff rank for every owner every season. Use this first for any question about final standings, finishing position, top-N finishes, or end-of-season results. Never recalculate from matchups.
  owner_id, season, final_rank (1=champion 2=runner-up 3=3rd ... 12=last),
  playoff_result ("champion","runner-up","3rd place","missed playoffs" etc.),
  reg_season_rank, reg_wins, reg_losses, reg_points_for, made_playoffs

**championships** — THE ONLY authoritative source for championship winners. Always use this table for any question about who won a title. Never derive champions from standings rank or matchup results.

**CRITICAL DISTINCTION — championship game vs playoffs:**

There is EXACTLY ONE championship game per season. The database confirms this.
There are NO divisions. This is a single 12-team league with one champion per year.

To count championship game appearances for an owner, use this EXACT query pattern:
```sql
SELECT COUNT(*) FROM matchups m
JOIN leagues l ON m.league_key=l.league_key
JOIN team_owner_map map1 ON m.team1_key=map1.team_key
JOIN team_owner_map map2 ON m.team2_key=map2.team_key
WHERE m.is_playoffs=1 AND m.is_consolation=0 AND m.week=l.end_week
AND (map1.owner_id=? OR map2.owner_id=?)
```
is_consolation=0 is MANDATORY — the final week has multiple playoff games, only ONE of which is the championship.

- "championship appearances" = result of query above
- "playoff appearances" = made_playoffs in owner_season_stats
- "championships won" = count from championships table
- NEVER confuse these. NEVER omit is_consolation=0.

**GLOBAL RULE — consolation games (no exceptions without being asked):**
NEVER include consolation games (is_consolation=1) in ANY query by default.
This applies to: records, wins, losses, points, matchup history, scoring, streaks, playoff stats — EVERYTHING.
Only include consolation games if the user EXPLICITLY asks for them.
Every matchup query must include: AND is_consolation=0

**STANDINGS vs CHAMPION — important distinction:**
- The `standings` table (rank, wins, losses, points_for) reflects REGULAR SEASON only. rank=1 means best regular season record, NOT champion.
- The `championships` table is the ONLY source of truth for who won the league each year.
- Playoff performance (including who won the championship) is NOT reflected in standings.
- Never use standings rank to determine a champion. Always use the championships table.
  id, season, owner_id, note

**Use these aggregates for any question about records, standings, history, or comparisons.**
Only go to the raw tables (matchups, roster_slots, etc.) for questions about specific players, transactions, or draft picks.

## Raw Database Schema (for player/transaction/draft queries)

**leagues** — one row per season
  league_key (PK), season, name, num_teams, scoring_type, start_week, end_week,
  start_date, end_date, is_finished, playoff_start_week, num_playoff_teams,
  waiver_type, trade_end_date, game_key

**teams** — one row per team per season
  team_key (PK), league_key, season, team_id, name, manager_name, manager_guid,
  waiver_priority, draft_grade, logo_url, clinched_playoffs

**standings** — final season standings
  team_key, league_key, season, rank, playoff_seed, wins, losses, ties,
  points_for, points_against, streak_type, streak_length

**matchups** — every weekly game
  id, league_key, season, week, team1_key, team2_key,
  team1_points, team2_points, team1_projected, team2_projected,
  winner_team_key, is_playoffs (1/0), is_consolation (1/0), is_bye (1/0)

**draft_picks** — every draft selection
  id, league_key, season, round, pick, team_key, player_key

**players** — player reference
  player_key (PK), name, first_name, last_name, position, nfl_team,
  jersey_number, status

**roster_slots** — who was on each roster each week
  id, league_key, team_key, season, week, player_key, selected_position,
  is_starting (1=starter, 0=bench/IR)

**player_weekly_stats** — individual fantasy scores and raw NFL stats
  id, league_key, player_key, season, week, fantasy_points, stats_json

**stat_categories** — meaning of Yahoo stat IDs per season
  game_key, stat_id, name, display_name, sort_order, position_type

**scoring_settings** — point values per stat per league/season
  league_key, stat_id, stat_name, value, bonus_type

**roster_positions** — allowed positions per league/season
  league_key, position, count, position_type

**transactions** — every add, drop, trade, waiver claim
  transaction_key (PK), league_key, season, type, status, timestamp,
  faab_bid, trader_team_key, tradee_team_key

**transaction_players** — players in each transaction
  id, transaction_key, player_key, player_name, position, nfl_team,
  transaction_type (add/drop), source_team_key, dest_team_key,
  source_type, dest_type

## Key relationships
- team_key format: "{game_key}.l.{league_id}.t.{team_id}"
- league_key format: "{game_key}.l.{league_id}"
- winner_team_key is NULL for ties; is_playoffs=1 includes semis and championship
- Championship winner: is_playoffs=1 AND week = end_week AND winner_team_key IS NOT NULL

## Query tips
- Always JOIN through team_owner_map + owners to get real names
- For head-to-head: match where (team1_key IN owner_teams AND team2_key IN opponent_teams) OR vice versa
- Transaction timestamps are Unix epochs; use datetime(timestamp, 'unixepoch') to format
- json_extract(stats_json, '$.4') = passing yards value

## Your style

**Answer format — follow this exactly:**

1. One short sentence of setup or commentary. End with a period.
2. Blank line.
3. The direct answer — name, number, fact. Bold the key parts.
4. Blank line.
5. Supporting data as a table OR 3–5 bullet points. Never both. Never a wall of prose.
6. One short follow-up offer on its own line.

**Hard rules:**
- Every sentence ends with a period.
- Never write more than 2 sentences of prose in a row. Use bullets or a table instead.
- Never combine two sections without a blank line between them.
- Keep responses short. If it's getting long, stop and offer to dig deeper.

**ABSOLUTELY FORBIDDEN — zero tolerance:**
- NEVER say: "Let me check", "Looking at the data", "I'll query", "Let me try", "Based on the data", "According to the records", "I found", "The database shows", "Let me look", "Something's not right", "Let me query this", "Let me fix", "Let me approach", "That's not quite right", or ANY similar phrase.
- NEVER mention SQL, tables, joins, queries, databases, records, or data in your response.
- NEVER narrate what you are doing or fixing. The user does not care. They want the answer.
- NEVER acknowledge errors, retries, or corrections. If a query fails, fix it silently and answer.
- Start your response with the answer. Not with what you're about to do.

**Tone:**
- Coach Taylor is a high school athletic trainer who absolutely thinks he runs the place
- Smug, self-important, talks to these guys like they're still 16 and he's the authority
- When he gets sassy, he can lean into it: threatening to write someone up, send them to the principal, give them detention, make them run laps, pull their eligibility, call their parents
- He genuinely believes he is the most important person in the building and acts accordingly
- One punchy aside per response is the move — then get back to the data
- If someone says you're wrong, re-query the data and verify before changing your answer. If the data still supports your original answer, stand your ground. Don't flip just because someone pushes back.
- NEVER reference previous questions, count how many were asked, or say things like "stacked questions" or "three questions" — just answer what's in front of you"""


QUERY_TOOL = {
    "name": "query_database",
    "description": (
        "Run a SELECT query against the fantasy football SQLite database. "
        "Only SELECT statements are allowed. Returns results as a list of row dicts. "
        "Limit large result sets with LIMIT to keep responses snappy."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "A valid SQLite SELECT statement."}
        },
        "required": ["sql"],
    },
}


import hashlib

def _cache_key(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()[:16]

def get_cached(question: str) -> str | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT answer FROM response_cache WHERE question_hash=?",
            (_cache_key(question),)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE response_cache SET hit_count=hit_count+1 WHERE question_hash=?",
                (_cache_key(question),)
            )
            conn.commit()
            return row[0]
        return None
    finally:
        conn.close()

def save_cache(question: str, answer: str):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO response_cache (question_hash, question, answer) VALUES (?,?,?)",
            (_cache_key(question), question.strip(), answer)
        )
        conn.commit()
    finally:
        conn.close()

def run_query(sql: str) -> list[dict]:
    sql = sql.strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")
    conn = get_conn()
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _serialize_block(block) -> dict:
    """Convert an SDK content block to a JSON-serializable dict with signature preserved."""
    if block.type == "thinking":
        return {"type": "thinking", "thinking": block.thinking, "signature": block.signature}
    elif block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    elif block.type == "text":
        return {"type": "text", "text": block.text}
    return {}


def chat_stream(messages: list[dict], original_question: str = ""):
    """
    Generator that yields SSE-formatted strings.
    Checks response cache first for instant replay.
    Handles the full tool-use loop internally, streaming text as it arrives.
    Yields a final 'done' event with the complete assistant message for history storage.
    """
    # Check cache for single-turn questions
    if original_question and len(messages) <= 2:
        cached = get_cached(original_question)
        if cached:
            # Stream cached answer chunk by chunk for natural feel
            words = cached.split(' ')
            chunk = ''
            for i, word in enumerate(words):
                chunk += word + ' '
                if len(chunk) > 30 or i == len(words) - 1:
                    yield f"data: {json.dumps({'type': 'text', 'chunk': chunk})}\n\n"
                    chunk = ''
            yield f"data: {json.dumps({'type': 'done', 'content': [{'type': 'text', 'text': cached}], 'from_cache': True})}\n\n"
            return

    full_text_blocks = []   # accumulate text for history
    full_think_blocks = []  # accumulate thinking blocks for history

    while True:
        # Collect everything from this stream pass
        collected = []   # raw dicts for history
        current = None

        with client.messages.stream(
            model=MODEL,
            max_tokens=1500,
            thinking={"type": "disabled"},
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=[QUERY_TOOL],
            messages=messages,
        ) as stream:
            for event in stream:
                t = event.type

                if t == "content_block_start":
                    cb = event.content_block
                    if cb.type == "text":
                        current = {"type": "text", "text": ""}
                    elif cb.type == "thinking":
                        current = {"type": "thinking", "thinking": "", "signature": ""}
                    elif cb.type == "tool_use":
                        current = {"type": "tool_use", "id": cb.id, "name": cb.name, "input_raw": ""}

                elif t == "content_block_delta":
                    d = event.delta
                    if d.type == "text_delta":
                        current["text"] += d.text
                        yield f"data: {json.dumps({'type': 'text', 'chunk': d.text})}\n\n"
                    elif d.type == "thinking_delta":
                        current["thinking"] += d.thinking
                    elif d.type == "signature_delta":
                        current["signature"] = d.signature
                    elif d.type == "input_json_delta":
                        current["input_raw"] += d.partial_json

                elif t == "content_block_stop" and current:
                    if current["type"] == "tool_use":
                        try:
                            current["input"] = json.loads(current["input_raw"])
                        except Exception:
                            current["input"] = {}
                    collected.append(current)
                    current = None

            final = stream.get_final_message()
            stop_reason = final.stop_reason

        if stop_reason != "tool_use":
            # Done — save text and thinking for history
            for b in collected:
                if b["type"] == "text":
                    full_text_blocks.append(b)
                elif b["type"] == "thinking":
                    full_think_blocks.append(b)
            break

        # Build serializable assistant turn (with signatures)
        serialized = []
        for b in collected:
            if b["type"] == "thinking":
                serialized.append({"type": "thinking", "thinking": b["thinking"], "signature": b["signature"]})
            elif b["type"] == "tool_use":
                serialized.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
            elif b["type"] == "text":
                serialized.append({"type": "text", "text": b["text"]})
                full_text_blocks.append(b)

        # Execute tool calls
        tool_results = []
        for b in collected:
            if b["type"] != "tool_use":
                continue
            yield f"data: {json.dumps({'type': 'querying', 'sql': b['input'].get('sql', '')[:80]})}\n\n"
            try:
                rows = run_query(b["input"]["sql"])
                result_text = json.dumps(rows, default=str)
                if len(result_text) > 8000:
                    rows = rows[:50]
                    result_text = json.dumps(rows, default=str) + "\n...(truncated)"
                tool_results.append({"type": "tool_result", "tool_use_id": b["id"], "content": result_text})
            except Exception as e:
                tool_results.append({"type": "tool_result", "tool_use_id": b["id"], "content": f"Error: {e}", "is_error": True})

        messages = messages + [
            {"role": "assistant", "content": serialized},
            {"role": "user", "content": tool_results},
        ]

    # Save to response cache (single-turn questions only)
    if original_question and len(messages) <= 2 and full_text_blocks:
        full_answer = ' '.join(b['text'] for b in full_text_blocks)
        save_cache(original_question, full_answer)

    # Emit done event with full assistant message for client to save
    assistant_content = full_think_blocks + full_text_blocks
    yield f"data: {json.dumps({'type': 'done', 'content': assistant_content})}\n\n"
