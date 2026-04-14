/**
 * CameraScreen – Lader brugeren tage et foto med kameraet
 * eller vælge et billede fra biblioteket.
 * Sender billedet til backend og navigerer til ResultScreen.
 *
 * Backend URL sættes via EXPO_PUBLIC_API_URL-miljøvariablen
 * (standardværdi: http://localhost:8000).
 */
import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Image,
  SafeAreaView,
  ScrollView,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CameraScreen({ navigation }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  // ── Billedvalg ─────────────────────────────────────────────────────────────

  async function pickFromCamera() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Tilladelse nægtet', 'Appen har brug for adgang til kameraet.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (!result.canceled) {
      setPreview(result.assets[0]);
    }
  }

  async function pickFromLibrary() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Tilladelse nægtet', 'Appen har brug for adgang til fotobiblioteket.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (!result.canceled) {
      setPreview(result.assets[0]);
    }
  }

  // ── Send til backend ────────────────────────────────────────────────────────

  async function analyze() {
    if (!preview) {
      Alert.alert('Intet billede', 'Vælg eller tag et billede først.');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: preview.uri,
        name: 'board.jpg',
        type: 'image/jpeg',
      });

      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail ?? `Serverfejl (${response.status})`);
      }

      const data = await response.json();
      navigation.navigate('Result', { result: data, imageUri: preview.uri });
    } catch (e) {
      Alert.alert('Fejl', e.message ?? 'Kunne ikke forbinde til serveren.');
    } finally {
      setLoading(false);
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.inner}>
        {/* Forhåndsvisning */}
        {preview ? (
          <Image source={{ uri: preview.uri }} style={styles.preview} resizeMode="contain" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>Intet billede valgt</Text>
          </View>
        )}

        {/* Knapper */}
        <TouchableOpacity style={styles.btnPrimary} onPress={pickFromCamera} disabled={loading}>
          <Text style={styles.btnText}>📷  Brug kamera</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btnSecondary} onPress={pickFromLibrary} disabled={loading}>
          <Text style={styles.btnTextSecondary}>🖼️  Vælg fra bibliotek</Text>
        </TouchableOpacity>

        {preview && (
          <TouchableOpacity
            style={[styles.btnAnalyze, loading && styles.btnDisabled]}
            onPress={analyze}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#1a1a2e" />
            ) : (
              <Text style={styles.btnTextAnalyze}>🔍  Beregn point</Text>
            )}
          </TouchableOpacity>
        )}

        {loading && (
          <Text style={styles.loadingText}>Analyserer dit bræt … et øjeblik</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  inner: { alignItems: 'center', padding: 20, paddingBottom: 40 },
  preview: {
    width: '100%',
    height: 280,
    borderRadius: 12,
    marginBottom: 20,
    backgroundColor: '#0d0d1a',
  },
  placeholder: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#444466',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  placeholderText: { color: '#666688', fontSize: 15 },
  btnPrimary: {
    width: '100%',
    backgroundColor: '#FFD700',
    paddingVertical: 14,
    borderRadius: 28,
    alignItems: 'center',
    marginBottom: 12,
    elevation: 3,
  },
  btnText: { color: '#1a1a2e', fontSize: 16, fontWeight: 'bold' },
  btnSecondary: {
    width: '100%',
    borderWidth: 2,
    borderColor: '#FFD700',
    paddingVertical: 13,
    borderRadius: 28,
    alignItems: 'center',
    marginBottom: 20,
  },
  btnTextSecondary: { color: '#FFD700', fontSize: 16, fontWeight: '600' },
  btnAnalyze: {
    width: '100%',
    backgroundColor: '#28a745',
    paddingVertical: 15,
    borderRadius: 28,
    alignItems: 'center',
    elevation: 4,
  },
  btnDisabled: { opacity: 0.6 },
  btnTextAnalyze: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  loadingText: { color: '#aaaacc', marginTop: 14, fontSize: 14 },
});
