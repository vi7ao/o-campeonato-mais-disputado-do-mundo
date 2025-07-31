from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import json

# DISCLAIMER: esses dados estão sendo buscados no dia 30/07/2025, com todas as equipes com 19 jogos.
# isso está sendo feito para estudos e análise, sem fins lucrativos
# obrigado api do sofascore por existir

# variaveis do sofascore
TOURNAMENT_ID = 390 # brasileirao serie b
SEASON_ID = 72603 # temporada de 2025

def setup_driver():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def get_team_stats_selenium(driver, team_id):
    url = f"https://www.sofascore.com/api/v1/team/{team_id}/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/statistics/overall"
    try:
        driver.get(url)
        time.sleep(2)
        data = json.loads(driver.find_element("tag name", "pre").text)
        return data.get('statistics', {})
    except Exception as e:
        print(f"erro selenium: {e}")
        return None

# slug: id, nome do time
clubes = {
    'goias':                  {'id': 1960,    'name': 'Goiás'},
    'coritiba':               {'id': 1982,    'name': 'Coritiba'},
    'novorizontino':          {'id': 135514,  'name': 'Novorizontino'},
    'chapecoense':            {'id': 21845,   'name': 'Chapecoense'},
    'remo':                   {'id': 2012,    'name': 'Remo'},
    'criciuma':               {'id': 1984,    'name': 'Criciúma'},
    'cuiaba':                 {'id': 49202,   'name': 'Cuiabá'},
    'avai':                   {'id': 7315,    'name': 'Avaí'},
    'vila-nova':              {'id': 2021,    'name': 'Vila Nova FC'},
    'crb':                    {'id': 22032,   'name': 'CRB'},
    'athletico':              {'id': 1967,    'name': 'Athletico'},
    'athletic-club':          {'id': 342775,  'name': 'Athletic Club'},
    'operario-pr':            {'id': 39634,   'name': 'Operário-PR'},
    'atletico-goianiense':    {'id': 7314,    'name': 'Atlético Goianiense'},
    'america-mineiro':        {'id': 1973,    'name': 'América Mineiro'},
    'volta-redonda':          {'id': 6982,    'name': 'Volta Redonda'},
    'paysandu-sc':            {'id': 1997,    'name': 'Paysandu SC'},
    'ferroviaria':            {'id': 35285,   'name': 'Ferroviária'},
    'amazonas-fc':            {'id': 336664,  'name': 'Amazonas FC'},
    'botafogo-sp':            {'id': 1979,    'name': 'Botafogo-SP'},
}

driver = setup_driver()
all_team_stats = []

print("Buscando as estatisticas!")
for team_key, team_info in clubes.items():
    team_id = team_info['id']
    team_name = team_info['name']
    
    print(f"comecando o get do {team_name}")
    
    stats = get_team_stats_selenium(driver, team_id)
    if stats:
        stats['team_id'] = team_id
        stats['team_name'] = team_name
        stats['team_key'] = team_key
        all_team_stats.append(stats)
        print(f"✓ {team_name} - deu boa!")
    else:
        print(f"✗ {team_name} - Failed")
    
    time.sleep(3)

driver.quit()
print(f"fim! {len(all_team_stats)} times completos")

# salvar csv
if all_team_stats:
    df = pd.DataFrame(all_team_stats)
    df.to_csv("estatisticas_serie_b.csv", index=False)
    print("salvo!")