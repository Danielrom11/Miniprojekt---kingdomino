/**
 * HomeScreen – Velkomstskærm med hero-billede og knap til at starte beregning.
 */
import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  SafeAreaView,
} from 'react-native';

const heroImage = require('../assets/hero.png');

export default function HomeScreen({ navigation }) {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />

      {/* Hero-billede */}
      <Image source={heroImage} style={styles.hero} resizeMode="contain" />

      {/* Titel */}
      <Text style={styles.title}>King Domino</Text>
      <Text style={styles.subtitle}>Pointberegner</Text>

      {/* Beregn-knap */}
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('Camera')}
        activeOpacity={0.85}
      >
        <Text style={styles.buttonText}>📸  Beregn point</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  hero: {
    width: '85%',
    height: 260,
    marginBottom: 28,
    borderRadius: 16,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFD700',
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaaacc',
    marginBottom: 48,
    marginTop: 4,
    letterSpacing: 1,
  },
  button: {
    backgroundColor: '#FFD700',
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 32,
    elevation: 4,
    shadowColor: '#FFD700',
    shadowOpacity: 0.4,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
  buttonText: {
    color: '#1a1a2e',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
});
