def get_neighbors(x, y, max_rows=5, max_cols=5):
    """
    Finder gyldige naboer (op, ned, venstre, højre).
    Ingen diagonaler, da reglerne specifikt nævner 'horizontally or vertically'.
    """
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [
        (x + dx, y + dy)
        for dx, dy in directions
        if 0 <= x + dx < max_rows and 0 <= y + dy < max_cols
    ]

def _find_cluster(start_x, start_y, tiles, visited, grid_rows, grid_cols, terrain_type):
    """
    Finds a single connected terrain cluster using BFS and returns its details.
    """
    tiles_to_check = [(start_x, start_y)]
    visited.add((start_x, start_y))
    
    area_tiles_count = 0
    area_crowns_count = 0
    cluster_coords = []

    while len(tiles_to_check) > 0:
        current_x, current_y = tiles_to_check.pop(0)
        cluster_coords.append((current_x, current_y))
        
        area_tiles_count += 1
        area_crowns_count += tiles[(current_x, current_y)].get("crowns", 0)
        
        neighbors = get_neighbors(current_x, current_y, grid_rows, grid_cols)
        
        for nx, ny in neighbors:
            if (nx, ny) not in visited and tiles.get((nx, ny), {}).get("terrain") == terrain_type:
                visited.add((nx, ny))
                tiles_to_check.append((nx, ny))
    
    return {
        "terrain": terrain_type,
        "tiles_count": area_tiles_count,
        "crowns_count": area_crowns_count,
        "score": area_tiles_count * area_crowns_count,
        "coordinates": cluster_coords
    }

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
    visited = set()
    clusters = []
    
    for x in range(grid_rows):
        for y in range(grid_cols):
            if (x, y) in visited or (x, y) not in tiles:
                continue
                
            terrain_type = tiles[(x, y)].get("terrain", "blank")
            
            if terrain_type.lower() == "blank":
                visited.add((x, y))
                continue
            
            # Find a new cluster starting from the current tile
            cluster_details = _find_cluster(x, y, tiles, visited, grid_rows, grid_cols, terrain_type)
            
            if cluster_details:
                total_score += cluster_details["score"]
                clusters.append(cluster_details)
            
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
