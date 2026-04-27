def get_neighbors(x, y, max_rows=5, max_cols=5):
    """Returnerer de gyldige naboer til et felt: op, ned, venstre og højre."""
    return [
        (neighbor_x, neighbor_y)
        for neighbor_x, neighbor_y in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        if 0 <= neighbor_x < max_rows and 0 <= neighbor_y < max_cols
    ]

def _find_cluster(start_x, start_y, tiles, visited, grid_rows, grid_cols, terrain_type):
    """Finder et sammenhængende område af samme terræn med BFS."""
    tiles_to_check = [(start_x, start_y)]
    visited.add((start_x, start_y))
    
    crowns_count = 0
    cluster_coords = []

    while tiles_to_check:
        current_x, current_y = tiles_to_check.pop(0)
        cluster_coords.append((current_x, current_y))
        crowns_count += tiles.get((current_x, current_y), {}).get("crowns", 0)
        
        for neighbor_x, neighbor_y in get_neighbors(current_x, current_y, grid_rows, grid_cols):
            if (neighbor_x, neighbor_y) not in visited and tiles.get((neighbor_x, neighbor_y), {}).get("terrain") == terrain_type:
                visited.add((neighbor_x, neighbor_y))
                tiles_to_check.append((neighbor_x, neighbor_y))
    
    tiles_count = len(cluster_coords)
    return {
        "terrain": terrain_type,
        "tiles_count": tiles_count,
        "crowns_count": crowns_count,
        "score": tiles_count * crowns_count,
        "coordinates": cluster_coords
    }

def calculate_score(tiles, grid_rows=5, grid_cols=5):
    """Beregner den samlede score for et King Domino spil, inklusiv bonusreglerne."""
    total_score = 0
    visited = set()
    clusters = []
    filled_tiles = 0
    bonus_messages = []
    
    for x in range(grid_rows):
        for y in range(grid_cols):
            terrain_type = tiles.get((x, y), {}).get("terrain", "blank")
            
            # Spring tomme felter over.
            if terrain_type.lower() == "blank":
                continue
                
            # Tæl alle udfyldte felter, så vi kan se om kingdomet er komplet.
            filled_tiles += 1
            
            # Hvis feltet ikke er besøgt endnu, finder vi et nyt sammenhængende område.
            if (x, y) not in visited:
                cluster = _find_cluster(x, y, tiles, visited, grid_rows, grid_cols, terrain_type)
                total_score += cluster["score"]
                clusters.append(cluster)
                
    # Bonusregel: Harmony giver +5 point, hvis hele boardet er udfyldt.
    if filled_tiles == grid_rows * grid_cols:
        total_score += 5  # Harmony: 5 point hvis hele pladen er udfyldt
        bonus_messages.append("Bonus: Harmony er opfyldt, så der gives +5 point.")
        
        center_x, center_y = grid_rows // 2, grid_cols // 2
        center_terrain = tiles.get((center_x, center_y), {}).get("terrain", "").lower()
        
        # Bonusregel: Middle Kingdom giver +10 point, hvis home-brikken står i midten.
        if center_terrain == "home":
            total_score += 10
            bonus_messages.append("Bonus: Home-brikken er i midten, så der gives +10 point.")
            
    return total_score, clusters, bonus_messages
