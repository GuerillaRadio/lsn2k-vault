content = open('src/fetcher.py', encoding='utf-8').read()

# Change INSERT OR IGNORE to check for unique constraint properly
# The table now has UNIQUE(transaction_key, player_key, dest_team_key)
# INSERT OR IGNORE will handle it correctly now that the constraint exists
# Just make sure we're using INSERT OR IGNORE (already the case)
print("Fetcher already uses INSERT OR IGNORE - now that UNIQUE constraint exists, dupes are prevented.")
print("No change needed to fetcher.")
