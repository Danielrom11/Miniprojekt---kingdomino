import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

const TERRAIN_COLORS = {
  Forest: '#2d6a4f',
  Field: '#ffd166',
  Mine: '#6c757d',
  Swamp: '#8b5e3c',
  Lake: '#4895ef',
  Grassland: '#95d5b2',
  blank: '#2c2c3e',
};

function TileGrid({ tiles }) {
  const grid = [];
  for (let y = 0; y < 5; y++) {
    const row = [];
    for (let x = 0; x < 5; x++) {
      const key = `${x},${y}`;
      const tile = tiles[key] ?? { terrain: 'blank', crowns: 0 };
      const bg = TERRAIN_COLORS[tile.terrain] ?? '#555';
      row.push(
        <View key={key} style={[styles.tile, { backgroundColor: bg }]}>
          <Text style={styles.tileTerrainText} numberOfLines={1}>
            {tile.terrain === 'blank' ? '' : tile.terrain.slice(0, 3)}
          </Text>
          {tile.crowns > 0 && (
            <Text style={styles.tileCrownText}>{'♛'.repeat(tile.crowns)}</Text>
          )}
        </View>
      );
    }
    grid.push(
      <View key={y} style={styles.row}>
        {row}
      </View>
    );
  }
  return <View style={styles.grid}>{grid}</View>;
}

function ClusterCard({ cluster, index }) {
  const bg = TERRAIN_COLORS[cluster.terrain] ?? '#555';
  return (
    <View style={[styles.clusterCard, { borderLeftColor: bg }]}>
      <Text style={styles.clusterTitle}>
        #{index + 1} {cluster.terrain}
      </Text>
      <Text style={styles.clusterDetail}>
        {cluster.tiles_count} tiles × {cluster.crowns_count} crowns ={' '}
        <Text style={styles.clusterScore}>{cluster.score} pts</Text>
      </Text>
    </View>
  );
}

export default function ResultsScreen({ route }) {
  const { result, imageUri } = route.params ?? {};
  const { total_score = 0, tiles = {}, clusters = [] } = result ?? {};

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Score banner */}
      <View style={styles.scoreBanner}>
        <Text style={styles.scoreLabel}>Total Score</Text>
        <Text style={styles.scoreValue}>{total_score}</Text>
      </View>

      {/* Board image (if available) */}
      {imageUri && (
        <Image source={{ uri: imageUri }} style={styles.boardImage} resizeMode="contain" />
      )}

      {/* Tile grid */}
      <Text style={styles.sectionTitle}>Board Overview</Text>
      <TileGrid tiles={tiles} />

      {/* Legend */}
      <View style={styles.legend}>
        {Object.entries(TERRAIN_COLORS)
          .filter(([t]) => t !== 'blank')
          .map(([terrain, color]) => (
            <View key={terrain} style={styles.legendItem}>
              <View style={[styles.legendSwatch, { backgroundColor: color }]} />
              <Text style={styles.legendLabel}>{terrain}</Text>
            </View>
          ))}
      </View>

      {/* Cluster breakdown */}
      <Text style={styles.sectionTitle}>Score Breakdown</Text>
      {clusters.length === 0 ? (
        <Text style={styles.noData}>No scoring clusters found.</Text>
      ) : (
        clusters.map((c, i) => <ClusterCard key={i} cluster={c} index={i} />)
      )}

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  content: { padding: 16 },

  scoreBanner: {
    backgroundColor: '#e0c060',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreLabel: { fontSize: 14, color: '#1a1a2e', fontWeight: '600', letterSpacing: 1 },
  scoreValue: { fontSize: 56, fontWeight: 'bold', color: '#1a1a2e' },

  boardImage: {
    width: '100%',
    height: 260,
    borderRadius: 12,
    marginBottom: 20,
  },

  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#e0c060',
    marginBottom: 10,
    marginTop: 4,
  },

  grid: { alignSelf: 'center', marginBottom: 16 },
  row: { flexDirection: 'row' },
  tile: {
    width: 60,
    height: 60,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 0.5,
    borderColor: 'rgba(255,255,255,0.15)',
    padding: 2,
  },
  tileTerrainText: { fontSize: 9, color: '#fff', fontWeight: '600' },
  tileCrownText: { fontSize: 11, color: '#ffd700' },

  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
    justifyContent: 'center',
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendSwatch: { width: 14, height: 14, borderRadius: 3 },
  legendLabel: { fontSize: 12, color: '#b0b8cc' },

  clusterCard: {
    backgroundColor: '#0f3460',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 5,
  },
  clusterTitle: { fontSize: 15, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  clusterDetail: { fontSize: 14, color: '#b0b8cc' },
  clusterScore: { color: '#e0c060', fontWeight: 'bold' },

  noData: { color: '#b0b8cc', fontStyle: 'italic', textAlign: 'center', marginBottom: 20 },
});
