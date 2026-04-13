def get_neighbors(x, y, max_rows=5, max_cols=5):
    """
    Finder gyldige naboer (op, ned, venstre, højre).
    Ingen diagonaler, da reglerne specifikt nævner 'horizontally or vertically'.
    """
    neighbors = []
    directions = [
        (-1, 0),  # op
        (1, 0),   # ned
        (0, -1),  # venstre
        (0, 1)    # højre
    ]
    
    for dx, dy in directions:
        new_x, new_y = x + dx, y + dy
        # Tjek om naboen er inden for pladens grænser (5x5 grid som standard)
        if 0 <= new_x < max_rows and 0 <= new_y < max_cols:
            neighbors.append((new_x, new_y))
            
    return neighbors

def calculate_score(tiles, grid_rows=5, grid_cols=5):
    """
    Beregner den samlede score for et King Domino spil.
    
    Forventer at 'tiles' er en dictionary med koordinater (x, y) som nøgler, f.eks.:
    tiles = {
        (0, 0): {"terrain": "Forest", "crowns": 1},
        (0, 1): {"terrain": "blank", "crowns": 0},
        # ... resten af pladen
    }
    """
    total_score = 0
    visited = set() # Holder styr på hvilke felter vi allerede har optalt
    clusters = []   # Gemmer detaljeret info om hvert fundet område
    
    # Gennemgå alle mulige felter på spillepladen (række for række)
    for x in range(grid_rows):
        for y in range(grid_cols):
            # Spring over, hvis vi allerede har talt dette felt som en del af et område
            if (x, y) in visited:
                continue
            
            # Tjek om koordinatet overhovedet findes i vores data
            if (x, y) not in tiles:
                continue
                
            tile_info = tiles[(x, y)]
            terrain_type = tile_info.get("terrain", "blank")
            
            # Vi ignorerer felter der er "blank" (kategoriseret som tomme pladser)
            if terrain_type.lower() == "blank":
                visited.add((x, y))
                continue
            
            # --- START PÅ ET NYT OMRÅDE (Cluster) ---
            area_tiles_count = 0
            area_crowns_count = 0
            cluster_coords = [] # Vi gemmer alle specifikke felter i dette område
            
            # Liste (queue) til at holde styr på næste felter vi skal tjekke i dette specifikke område
            tiles_to_check = [(x, y)]
            visited.add((x, y)) 
            
            # Kør så længe der er ubesøgte felter af samme type i dette område
            while len(tiles_to_check) > 0:
                current_x, current_y = tiles_to_check.pop(0)
                cluster_coords.append((current_x, current_y)) # Gem koordinatet
                
                # 1. Læg feltet og dets kroner til områdets total
                area_tiles_count += 1
                area_crowns_count += tiles[(current_x, current_y)].get("crowns", 0)
                
                # 2. Find naboer og tjek om de skal med i området
                neighbors = get_neighbors(current_x, current_y, grid_rows, grid_cols)
                
                for nx, ny in neighbors:
                    # Hvis naboen ikke er besøgt endnu og findes i vores plade
                    if (nx, ny) not in visited and (nx, ny) in tiles:
                        neighbor_terrain = tiles[(nx, ny)].get("terrain", "blank")
                        
                        # Hvis naboen har samme terræntype, tilhører den dette område
                        if neighbor_terrain == terrain_type:
                            visited.add((nx, ny))          # Markér som besøgt
                            tiles_to_check.append((nx, ny)) # Sæt i køen til at blive tjekket for dens egne naboer
            
            # --- OMRÅDET ER OPGJORT ---
            # Udregn point for området (antal sammenhængende felter * antal kroner)
            area_score = area_tiles_count * area_crowns_count
            total_score += area_score
            
            # Gem alle detaljerne ned i vores journal, hvis det altså er et rigtigt område
            clusters.append({
                "terrain": terrain_type,
                "tiles_count": area_tiles_count,
                "crowns_count": area_crowns_count,
                "score": area_score,
                "coordinates": cluster_coords
            })
            
    return total_score, clusters

# ==========================================
# EKSEMPEL PÅ TEST (Ground Truth)
# ==========================================
if __name__ == "__main__":
    # Testopsætning med at et lille udsnit af en plade
    # Her simulerer vi et 7-felters 'Forest' område med 3 kroner tilsammen, og et 'blank' felt
    dummy_tiles = {
        (0, 0): {"terrain": "Forest", "crowns": 1},
        (0, 1): {"terrain": "Forest", "crowns": 0},
        (0, 2): {"terrain": "Forest", "crowns": 2},
        (1, 0): {"terrain": "Forest", "crowns": 0},
        (1, 1): {"terrain": "Forest", "crowns": 0},
        (1, 2): {"terrain": "blank", "crowns": 0},
        (2, 0): {"terrain": "Forest", "crowns": 0},
        (2, 1): {"terrain": "Forest", "crowns": 0},
    }
    
    score, found_clusters = calculate_score(dummy_tiles, grid_rows=3, grid_cols=3)
    print(f"Forventet score for 7 skovfelter med 3 kroner: 21")
    print(f"Beregnet score: {score}")
    print("\n--- FUNDNE GRUPPER I TEST ---")
    for group in found_clusters:
        print(f"{group['terrain']} med {group['tiles_count']} felter * {group['crowns_count']} kroner = {group['score']} point")
