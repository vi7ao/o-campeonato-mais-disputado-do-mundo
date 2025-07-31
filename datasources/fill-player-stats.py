from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import json

# configurações
TOURNAMENT_ID = 390
SEASON_ID = 72603
MIN_GAMES = 8
LIMIT = 20  # volta para paginação

def setup_driver():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def get_stats_data(driver, fields, category_name):
    """busca dados de estatísticas específicas com paginação"""
    all_stats = {}
    offset = 0
    
    while True:
        url = f"https://www.sofascore.com/api/v1/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/statistics?limit={LIMIT}&order=-rating&offset={offset}&accumulation=total&fields={fields}&filters=appearances.GT.{MIN_GAMES}%2Cposition.in.G~D~M~F"
        
        try:
            print(f"buscando {category_name} - offset {offset}")
            driver.get(url)
            time.sleep(2)
            
            data = json.loads(driver.find_element("tag name", "pre").text)
            players = data.get('results', [])
            
            if not players:
                break
                
            for player_data in players:
                player_id = player_data['player']['id']
                player_stats = {k: v for k, v in player_data.items() 
                              if k not in ['player', 'team']}
                all_stats[player_id] = player_stats
                
            if len(players) < LIMIT:
                break
                
            offset += LIMIT
            
        except Exception as e:
            print(f"erro em {category_name} offset {offset}: {e}")
            break
    
    print(f"✓ {category_name}: {len(all_stats)} jogadores")
    return all_stats

def fetch_all_stats(driver):
    """busca todas as categorias de estatísticas"""
    
    stat_groups = {
        # attack stats
        'attack1': 'goals%2CtotalShots%2CgoalConversionPercentage%2CshotFromSetPiece%2CheadedGoals%2Coffsides',
        'attack2': 'bigChancesMissed%2CshotsOnTarget%2CpenaltiesTaken%2CfreeKickGoal%2CleftFootGoals%2CpenaltyConversion',
        'attack3': 'successfulDribbles%2CshotsOffTarget%2CpenaltyGoals%2CgoalsFromInsideTheBox%2CrightFootGoals%2CsetPieceConversion',
        'attack4': 'successfulDribblesPercentage%2CblockedShots%2CpenaltyWon%2CgoalsFromOutsideTheBox%2ChitWoodwork',
        
        # defensive stats  
        'defensive1': 'tackles%2CerrorLeadToGoal%2CcleanSheet%2Cinterceptions%2CerrorLeadToShot%2CpenaltyConceded',
        'defensive2': 'ownGoals%2CdribbledPast%2Cclearances',
        
        # passing stats
        'passing1': 'totalPasses%2CbigChancesCreated%2CaccurateFinalThirdPasses%2CaccurateLongBalls%2Cassists%2CaccuratePassesPercentage',
        'passing2': 'inaccuratePasses%2CaccurateOppositionHalfPasses%2CaccurateCrossesPercentage',
        
        # goalkeeper stats
        'goalkeeper1': 'saves%2CsavedShotsFromInsideTheBox%2Cpunches%2CcrossesNotClaimed%2CsavedShotsFromOutsideTheBox',
        'goalkeeper2': 'runsOut%2CsuccessfulRunsOut%2CgoalsConcededInsideTheBox%2CpenaltyFaced%2CpenaltySave%2CgoalsConcededOutsideTheBox',
        'goalkeeper3': 'highClaims',
        
        # general stats
        'general1': 'yellowCards%2CaerialDuelsWon%2CminutesPlayed%2CpossessionLost%2CredCards%2CaerialDuelsWonPercentage',
        'general2': 'wasFouled%2CgroundDuelsWon%2CtotalDuelsWon%2Cfouls%2CmatchesStarted',
        'general3': 'groundDuelsWonPercentage%2CtotalDuelsWonPercentage%2Cdispossessed%2Crating'
    }
    
    all_stats = {}
    
    for group_name, fields in stat_groups.items():
        stats = get_stats_data(driver, fields, group_name)
        
        # merge stats por player ID
        for player_id, player_stats in stats.items():
            if player_id not in all_stats:
                all_stats[player_id] = {}
            all_stats[player_id].update(player_stats)
        
        time.sleep(1)  # pausa entre requests
    
    return all_stats

def merge_player_data(players_df, stats_dict):
    """combina dados básicos dos jogadores com estatísticas"""
    
    # converte stats para dataframe
    stats_rows = []
    for player_id, stats in stats_dict.items():
        stats['playerId'] = player_id
        stats_rows.append(stats)
    
    if not stats_rows:
        print("nenhuma estatística encontrada")
        return players_df
        
    stats_df = pd.DataFrame(stats_rows)
    
    # merge com dados dos jogadores
    merged_df = players_df.merge(stats_df, on='playerId', how='left')
    
    print(f"dados combinados: {len(merged_df)} jogadores com {len(merged_df.columns)} colunas")
    return merged_df

def main():
    # carrega jogadores existentes
    try:
        players_df = pd.read_csv('jogadores_serie_b.csv')
        print(f"carregados {len(players_df)} jogadores do CSV")
    except FileNotFoundError:
        print("arquivo jogadores_serie_b.csv não encontrado")
        return
    
    # setup selenium
    driver = setup_driver()
    
    try:
        # busca todas as stats
        print("buscando estatísticas completas...")
        all_stats = fetch_all_stats(driver)
        
        # combina dados
        complete_df = merge_player_data(players_df, all_stats)
        
        # salva resultado
        output_file = 'jogadores_completos_serie_b.csv'
        complete_df.to_csv(output_file, index=False)
        
        print(f"✓ dados completos salvos em {output_file}")
        print(f"colunas: {list(complete_df.columns)}")
        
        # estatísticas
        print(f"\nresumo:")
        print(f"jogadores: {len(complete_df)}")
        print(f"colunas totais: {len(complete_df.columns)}")
        print(f"stats por posição:")
        print(complete_df['position'].value_counts().sort_index())
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()