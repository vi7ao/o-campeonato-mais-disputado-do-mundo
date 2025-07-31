from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import json

# DISCLAIMER: coleta de dados para análise e estudos, sem fins lucrativos

# configurações
TOURNAMENT_ID = 390  # brasileirao serie b
SEASON_ID = 72603    # temporada 2025
MIN_GAMES = 8        # minimo de jogos para incluir jogador
LIMIT = 20           # limite por página da API

def setup_driver():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def get_players_by_position(driver, position):
    all_players = []
    seen_players = set()  # evita duplicatas
    offset = 0
    
    while True:
        url = f"https://www.sofascore.com/api/v1/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/statistics?limit={LIMIT}&order=-rating&offset={offset}&accumulation=total&fields=appearances&filters=appearances.GT.{MIN_GAMES}%2Cposition.in.{position}"
        
        try:
            print(f"buscando {position} - offset {offset}")
            driver.get(url)
            time.sleep(2)
            
            data = json.loads(driver.find_element("tag name", "pre").text)
            players = data.get('results', [])
            
            if not players:
                print(f"sem jogadores no offset {offset}, parando")
                break
                
            new_players_count = 0
            # processa jogadores desta página
            for player_data in players:
                player_id = player_data['player']['id']
                
                # evita duplicatas
                if player_id not in seen_players:
                    seen_players.add(player_id)
                    player_info = {
                        'playerId': player_id,
                        'playerName': player_data['player']['name'],
                        'club': player_data['team']['name'],
                        'position': position,
                        'gamesPlayed': player_data['appearances']
                    }
                    all_players.append(player_info)
                    new_players_count += 1
            
            print(f"offset {offset}: {new_players_count} novos jogadores")
            
            # se não há novos jogadores ou menos que o limite, parar
            if len(players) < LIMIT:
                break
                
            offset += LIMIT
            
        except Exception as e:
            print(f"erro ao buscar {position} offset {offset}: {e}")
            break
    
    print(f"✓ {position}: {len(all_players)} jogadores únicos encontrados")
    return all_players

def scrape_all_players():
    """busca todos os jogadores de todas as posições"""
    driver = setup_driver()
    all_players = []
    
    positions = {
        'G': 'Goleiros',
        'D': 'Defensores', 
        'M': 'Meio-campistas',
        'F': 'Atacantes'
    }
    
    print(f"iniciando busca de jogadores (min {MIN_GAMES} jogos)")
    
    for pos_code, pos_name in positions.items():
        print(f"buscando {pos_name}...")
        players = get_players_by_position(driver, pos_code)
        all_players.extend(players)
        time.sleep(2)  # pausa entre posições
    
    driver.quit()
    print(f"total: {len(all_players)} jogadores coletados")
    
    return all_players

def save_to_csv(players_data, filename="jogadores_serie_b.csv"):
    if not players_data:
        print("nenhum dado para salvar")
        return
    
    df = pd.DataFrame(players_data)
    df = df.sort_values(['position', 'gamesPlayed'], ascending=[True, False])
    df.to_csv(filename, index=False)
    
    print(f"✓ dados salvos em {filename}")
    print(f"resumo por posição:")
    print(df['position'].value_counts().sort_index())

if __name__ == "__main__":
    # executa scraping
    players = scrape_all_players()
    
    # salva em csv
    save_to_csv(players)
    
    # mostra primeiros resultados
    if players:
        df = pd.DataFrame(players)
        print("\nprimeiros 10 registros:")
        print(df.head(10).to_string(index=False))