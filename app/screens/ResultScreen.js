/**
 * ResultScreen – Viser beregningsresultatet:
 *   • Samlet score
 *   • Antal kroner fundet
 *   • Detaljer per cluster
 *   • Session-log (de seneste beregninger i denne kørsel)
 *
 * Den modtager { result, imageUri } via route.params.
 */
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

// Session-log opbevares i hukommelsen (nulstilles ved app-genstart)
const sessionLog = [];

export default function ResultScreen({ route, navigation }) {
  const { result, imageUri } = route.params ?? {};
  const [log, setLog] = useState([...sessionLog]);

  // Tilføj til session-log første gang skærmen vises med et nyt resultat
  useFocusEffect(
    useCallback(() => {
      if (result) {
        const entry = {
          id: Date.now().toString(),
          score: result.score,
          crowns: result.crowns_found,
          clusters: result.clusters_count,
          tidspunkt: new Date().toLocaleTimeString('da-DK'),
        };
        sessionLog.unshift(entry);
        setLog([...sessionLog]);
      }
    }, [result])
  );

  if (!result) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>Ingen data at vise.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.inner}>

        {/* ── Billedforhåndsvisning ── */}
        {imageUri && (
          <Image source={{ uri: imageUri }} style={styles.boardImage} resizeMode="contain" />
        )}

        {/* ── Score-badge ── */}
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreLabel}>Samlet score</Text>
          <Text style={styles.scoreValue}>{result.score}</Text>
        </View>

        {/* ── Oversigt ── */}
        <View style={styles.row}>
          <InfoCard label="Kroner fundet" value={result.crowns_found} icon="👑" />
          <InfoCard label="Områder" value={result.clusters_count} icon="🗺️" />
        </View>

        {/* ── Cluster-detaljer ── */}
        {result.clusters && result.clusters.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Detaljer per område</Text>
            {result.clusters.map((c, i) => (
              <View key={i} style={styles.clusterCard}>
                <Text style={styles.clusterTitle}>
                  {i + 1}. {c.terrain}
                </Text>
                <Text style={styles.clusterLine}>
                  {c.tiles_count} felter × {c.crowns_count} kroner ={' '}
                  <Text style={styles.clusterScore}>{c.score} point</Text>
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* ── Session-log ── */}
        {log.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Session-log</Text>
            {log.map((entry) => (
              <View key={entry.id} style={styles.logRow}>
                <Text style={styles.logTime}>{entry.tidspunkt}</Text>
                <Text style={styles.logDetail}>
                  Score: <Text style={styles.logHighlight}>{entry.score}</Text>
                  {'  '}👑 {entry.crowns}
                  {'  '}🗺️ {entry.clusters}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* ── Beregn ny plade ── */}
        <TouchableOpacity
          style={styles.newButton}
          onPress={() => navigation.navigate('Camera')}
          activeOpacity={0.85}
        >
          <Text style={styles.newButtonText}>🔄  Beregn ny plade</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.homeButton}
          onPress={() => navigation.navigate('Home')}
          activeOpacity={0.85}
        >
          <Text style={styles.homeButtonText}>🏠  Startside</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoCard({ label, value, icon }) {
  return (
    <View style={styles.infoCard}>
      <Text style={styles.infoIcon}>{icon}</Text>
      <Text style={styles.infoValue}>{value}</Text>
      <Text style={styles.infoLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  inner: { alignItems: 'center', padding: 20, paddingBottom: 48 },
  errorText: { color: '#ff6666', fontSize: 16, marginTop: 40 },

  boardImage: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    marginBottom: 20,
    backgroundColor: '#0d0d1a',
  },

  scoreBadge: {
    backgroundColor: '#FFD700',
    borderRadius: 60,
    width: 130,
    height: 130,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    elevation: 6,
    shadowColor: '#FFD700',
    shadowOpacity: 0.5,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
  },
  scoreLabel: { color: '#1a1a2e', fontSize: 12, fontWeight: '600', letterSpacing: 0.5 },
  scoreValue: { color: '#1a1a2e', fontSize: 52, fontWeight: 'bold', lineHeight: 58 },

  row: { flexDirection: 'row', gap: 16, marginBottom: 24 },
  infoCard: {
    flex: 1,
    backgroundColor: '#252540',
    borderRadius: 12,
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 8,
  },
  infoIcon: { fontSize: 26, marginBottom: 4 },
  infoValue: { color: '#FFD700', fontSize: 28, fontWeight: 'bold' },
  infoLabel: { color: '#aaaacc', fontSize: 12, marginTop: 2 },

  section: { width: '100%', marginBottom: 24 },
  sectionTitle: {
    color: '#FFD700',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    letterSpacing: 0.5,
  },
  clusterCard: {
    backgroundColor: '#252540',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  clusterTitle: { color: '#ffffff', fontSize: 14, fontWeight: '600', marginBottom: 2 },
  clusterLine: { color: '#aaaacc', fontSize: 13 },
  clusterScore: { color: '#28a745', fontWeight: 'bold' },

  logRow: {
    backgroundColor: '#1e1e38',
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logTime: { color: '#666688', fontSize: 12 },
  logDetail: { color: '#ccccee', fontSize: 13 },
  logHighlight: { color: '#FFD700', fontWeight: 'bold' },

  newButton: {
    width: '100%',
    backgroundColor: '#FFD700',
    paddingVertical: 15,
    borderRadius: 28,
    alignItems: 'center',
    marginBottom: 12,
    elevation: 4,
  },
  newButtonText: { color: '#1a1a2e', fontSize: 17, fontWeight: 'bold' },

  homeButton: {
    width: '100%',
    borderWidth: 2,
    borderColor: '#555577',
    paddingVertical: 13,
    borderRadius: 28,
    alignItems: 'center',
  },
  homeButtonText: { color: '#aaaacc', fontSize: 15 },
});
