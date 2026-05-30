import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Carson vs Garlich from owner_h2h:")
for r in conn.execute("""
    SELECT o1.nickname as owner1, o2.nickname as owner2,
           h.wins, h.losses, h.ties, h.points_for, h.points_against
    FROM owner_h2h h
    JOIN owners o1 ON h.owner1_id=o1.owner_id
    JOIN owners o2 ON h.owner2_id=o2.owner_id
    WHERE (o1.nickname='Carson' AND o2.nickname='Garlich')
       OR (o1.nickname='Garlich' AND o2.nickname='Carson')
""").fetchall():
    print(f"  {r['owner1']} vs {r['owner2']}: {r['wins']}W-{r['losses']}L")

print("\nVerify from raw matchups (regular season only):")
r = conn.execute("""
    SELECT
        SUM(CASE WHEN map1.owner_id=(SELECT owner_id FROM owners WHERE nickname='Carson') THEN 1 ELSE 0 END) as carson_as_t1,
        SUM(CASE WHEN map2.owner_id=(SELECT owner_id FROM owners WHERE nickname='Carson') THEN 1 ELSE 0 END) as carson_as_t2,
        SUM(CASE WHEN winner_key=map1.owner_id AND map1.owner_id=(SELECT owner_id FROM owners WHERE nickname='Carson') THEN 1
             WHEN winner_key=map2.owner_id AND map2.owner_id=(SELECT owner_id FROM owners WHERE nickname='Carson') THEN 1 ELSE 0 END) as carson_wins
    FROM (
        SELECT m.winner_team_key,
               map1.owner_id as o1, map2.owner_id as o2,
               map1.owner_id as owner1_id, map2.owner_id as owner2_id,
               map1, map2
        FROM matchups m
        JOIN team_owner_map map1 ON m.team1_key=map1.team_key
        JOIN team_owner_map map2 ON m.team2_key=map2.team_key
        WHERE m.is_playoffs=0 AND m.is_consolation=0
    )
""").fetchone()

# Simpler approach
rows = conn.execute("""
    SELECT m.winner_team_key, map1.owner_id as o1_id, map2.owner_id as o2_id,
           o1.nickname as o1, o2.nickname as o2
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    WHERE m.is_playoffs=0 AND m.is_consolation=0
    AND ((o1.nickname='Carson' AND o2.nickname='Garlich')
      OR (o1.nickname='Garlich' AND o2.nickname='Carson'))
""").fetchall()

carson_wins = 0
garlich_wins = 0
for r in rows:
    winner_is_t1 = r['winner_team_key'] is not None
    if (r['o1'] == 'Carson' and winner_is_t1) or (r['o2'] == 'Carson' and not winner_is_t1):
        pass  # need team keys not owner_id

# Count from matchups directly
print(f"  Total games between them: {len(rows)}")
# Check owner_h2h which was built from matchups
print("\nAll h2h rows involving Carson or Garlich:")
for r in conn.execute("""
    SELECT o1.nickname, o2.nickname, h.wins, h.losses
    FROM owner_h2h h
    JOIN owners o1 ON h.owner1_id=o1.owner_id
    JOIN owners o2 ON h.owner2_id=o2.owner_id
    WHERE o1.nickname IN ('Carson','Garlich') AND o2.nickname IN ('Carson','Garlich')
""").fetchall():
    print(f"  {r[0]} wins={r[2]}, losses={r[3]} vs {r[1]}")
    print(f"  => {r[0]} is {r[2]}-{r[3]} vs {r[1]}")

conn.close()
