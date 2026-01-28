# Yahoo Fantasy Sports API Guide

## Overview

The Yahoo Fantasy Sports API provides access to fantasy league data including rosters, standings, matchups, transactions, and player statistics. This document covers integration for the humor agent project.

## Authentication

Yahoo uses **OAuth 2.0** for authentication. You'll need to register an app at the Yahoo Developer Console.

### Setup Steps

1. Go to https://developer.yahoo.com/apps/
2. Click "Create an App"
3. Select "Installed Application" (for CLI tools) or "Web Application"
4. Request the `fspt-r` (fantasy sports read) permission
5. Note your **Client ID** and **Client Secret**

### OAuth Flow

```python
from yahoo_oauth import OAuth2

# First time: opens browser for authorization
oauth = OAuth2(None, None, from_file='oauth_token.json')

# Subsequent runs: uses cached token
if not oauth.token_is_valid():
    oauth.refresh_access_token()
```

## Python Library: yahoo-fantasy-api

The recommended library is `yahoo-fantasy-api` which wraps the REST API.

```bash
pip install yahoo-fantasy-api
```

### Basic Usage

```python
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import League, Game

# Initialize OAuth
oauth = OAuth2(None, None, from_file='oauth_token.json')

# Get your fantasy baseball game
gm = Game(oauth, 'mlb')

# Get your league (you need the league ID)
league_id = 'YOUR_LEAGUE_ID'  # Found in your league URL
lg = gm.to_league(league_id)

# Get league info
print(lg.settings())
print(lg.standings())
print(lg.matchups())
```

## Key Endpoints for Humor Content

### 1. Standings & Scores (Weekly Roasts)

```python
# Get current standings
standings = lg.standings()
# Returns: team names, wins, losses, points

# Get weekly matchups
matchups = lg.matchups()
# Returns: who played who, scores, winner/loser
```

**Humor gold**: Who got crushed? Who barely won? Who's in last place?

### 2. Roster & Lineup Decisions

```python
# Get a team's roster
team = lg.to_team('team_key')
roster = team.roster()

# Check who was benched
for player in roster:
    if player['selected_position'] == 'BN':
        print(f"Benched: {player['name']}")
```

**Humor gold**: Someone benched their best player? Didn't start a pitcher who threw a no-hitter?

### 3. Transactions (Trades & Pickups)

```python
# Get recent transactions
transactions = lg.transactions('add,drop,trade')

# Filter by type
adds = [t for t in transactions if t['type'] == 'add']
trades = [t for t in transactions if t['type'] == 'trade']
```

**Humor gold**: Lopsided trades, panic drops, waiver wire steals

### 4. Player Stats

```python
# Get player stats
player = lg.player_stats(['player_key'], 'lastweek')
# Compare projected vs actual performance
```

**Humor gold**: Player busts, surprise performances, "experts" being wrong

### 5. League Metadata

```python
# Team names and managers
teams = lg.teams()
for team_key, team_info in teams.items():
    print(team_info['name'], team_info['managers'])
```

## Rate Limits

Yahoo's API has rate limits (not officially documented, but observed):
- ~2000 requests per hour per user
- Respect `Retry-After` headers if you get 429 errors
- Cache responses when possible

## Data Structure for Humor Agent

Recommended daily data pull:

```python
def get_daily_humor_data(league):
    """Pull all data needed for daily humor email."""
    return {
        'standings': league.standings(),
        'matchups': league.matchups(),
        'transactions': league.transactions('add,drop,trade', count=20),
        'scoreboard': league.scoreboard(),
        # Add player of the day, worst performance, etc.
    }
```

## Example: Finding Roast-Worthy Moments

```python
def find_biggest_blowout(matchups):
    """Find the most lopsided matchup of the week."""
    biggest_margin = 0
    worst_loss = None

    for matchup in matchups:
        team1, team2 = matchup['teams']
        margin = abs(team1['points'] - team2['points'])

        if margin > biggest_margin:
            biggest_margin = margin
            loser = team1 if team1['points'] < team2['points'] else team2
            winner = team2 if team1['points'] < team2['points'] else team1
            worst_loss = {
                'loser': loser['name'],
                'winner': winner['name'],
                'margin': margin,
            }

    return worst_loss

def find_benched_stars(team, threshold=20):
    """Find high-scoring players left on the bench."""
    benched_stars = []

    for player in team.roster():
        if player['selected_position'] == 'BN':
            points = player.get('points', 0)
            if points >= threshold:
                benched_stars.append({
                    'player': player['name'],
                    'points': points,
                    'position': player['eligible_positions'][0],
                })

    return benched_stars
```

## Environment Variables

```bash
# .env file
YAHOO_CLIENT_ID=your_client_id
YAHOO_CLIENT_SECRET=your_client_secret
YAHOO_LEAGUE_ID=your_league_id
```

## Resources

- [Yahoo Fantasy API Docs](https://developer.yahoo.com/fantasysports/guide/)
- [yahoo-fantasy-api PyPI](https://pypi.org/project/yahoo-fantasy-api/)
- [Yahoo Developer Console](https://developer.yahoo.com/apps/)
