import requests, json, os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('STRATZ_API_KEY')

query = """
{
  matches(request: { take: 3 }) {
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

print(f'Статус: {r.status_code}')
print(r.text[:500])
