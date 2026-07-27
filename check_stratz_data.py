import requests, json, os
from dotenv import load_dotenv
import datetime

load_dotenv()
key = os.getenv('STRATZ_API_KEY')

query = """
{
  matches(request: { take: 3, isParsed: true }) {
    id
    radiantTeam { name }
    direTeam { name }
    didRadiantWin
    durationSeconds
    league { name }
    endDateTime
  }
}
"""

r = requests.post('https://api.stratz.com/graphql',
                   headers={'Authorization': f'Bearer {key}'},
                   json={'query': query})

data = r.json().get('data', {}).get('matches', [])
print(f'Статус: {r.status_code}, найдено матчей: {len(data)}\n')

for m in data:
    end = m.get('endDateTime', 0)
    date_str = datetime.datetime.fromtimestamp(end).strftime('%d.%m.%Y') if end else '?'
    print(f'Матч {m["id"]}:')
    print(f'  {m.get("radiantTeam",{}).get("name","?")} vs {m.get("direTeam",{}).get("name","?")}')
    print(f'  Турнир: {m.get("league",{}).get("name","?")}')
    print(f'  Дата: {date_str} | Победа Radiant: {m.get("didRadiantWin")}')
    print()
