import requests, json, os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('STRATZ_API_KEY')

# Сначала получим live-матчи (они содержат ID)
query1 = """
{
  live {
    matches {
      matchId
    }
  }
}
"""

r1 = requests.post('https://api.stratz.com/graphql',
                    headers={'Authorization': f'Bearer {key}'},
                    json={'query': query1})

print(f'Live статус: {r1.status_code}')
print(r1.text[:300])

# Попробуем другой подход - ищем по турнирам
query2 = """
{
  leagues(request: { take: 3 }) {
    id
    name
  }
}
"""

r2 = requests.post('https://api.stratz.com/graphql',
                    headers={'Authorization': f'Bearer {key}'},
                    json={'query': query2})

print(f'\nЛиги статус: {r2.status_code}')
print(r2.text[:300])
