import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';

// Change this to your backend host when deploying.
// For local development with Expo Go on a physical device, use your machine's LAN IP.
const API_BASE_URL = 'http://localhost:8000';

export default function CameraScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [loading, setLoading] = useState(false);
  const cameraRef = useRef(null);

  useEffect(() => {
    if (permission && !permission.granted) {
      requestPermission();
    }
  }, [permission]);

  const sendImageToBackend = async (uri) => {
    setLoading(true);
    try {
      const formData = new FormData();
      const filename = uri.split('/').pop();
      const match = /\.(\w+)$/.exec(filename ?? '');
      const type = match ? `image/${match[1]}` : 'image/jpeg';
      formData.append('file', { uri, name: filename ?? 'photo.jpg', type });

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail ?? `Server error ${response.status}`);
      }

      const data = await response.json();
      navigation.navigate('Results', { result: data, imageUri: uri });
    } catch (error) {
      Alert.alert('Error', error.message ?? 'Failed to analyze image.');
    } finally {
      setLoading(false);
    }
  };

  const takePicture = async () => {
    if (!cameraRef.current) return;
    const photo = await cameraRef.current.takePictureAsync({ quality: 0.85 });
    await sendImageToBackend(photo.uri);
  };

  const pickFromLibrary = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!result.canceled && result.assets.length > 0) {
      await sendImageToBackend(result.assets[0].uri);
    }
  };

  if (!permission) {
    return <View style={styles.center}><ActivityIndicator color="#e0c060" size="large" /></View>;
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>Camera permission is required.</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} ref={cameraRef} facing="back">
        {/* Grid overlay to help align the board */}
        <View style={styles.gridOverlay} pointerEvents="none">
          {[1, 2, 3, 4].map((i) => (
            <View key={`h${i}`} style={[styles.gridLine, styles.horizontal, { top: `${i * 20}%` }]} />
          ))}
          {[1, 2, 3, 4].map((i) => (
            <View key={`v${i}`} style={[styles.gridLine, styles.vertical, { left: `${i * 20}%` }]} />
          ))}
        </View>
      </CameraView>

      <View style={styles.controls}>
        <TouchableOpacity style={styles.secondaryButton} onPress={pickFromLibrary} disabled={loading}>
          <Text style={styles.secondaryButtonText}>📁  Library</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.captureButton} onPress={takePicture} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#1a1a2e" size="large" />
          ) : (
            <Text style={styles.captureIcon}>⬤</Text>
          )}
        </TouchableOpacity>

        {/* Spacer to balance the layout */}
        <View style={styles.spacer} />
      </View>

      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#e0c060" />
          <Text style={styles.loadingText}>Analyzing board…</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  center: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  camera: { flex: 1 },
  gridOverlay: {
    ...StyleSheet.absoluteFillObject,
  },
  gridLine: {
    position: 'absolute',
    backgroundColor: 'rgba(255,255,255,0.25)',
  },
  horizontal: { left: 0, right: 0, height: 1 },
  vertical: { top: 0, bottom: 0, width: 1 },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#e0c060',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureIcon: { fontSize: 36, color: '#1a1a2e' },
  secondaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e0c060',
  },
  secondaryButtonText: { color: '#e0c060', fontSize: 14 },
  spacer: { width: 80 },
  message: { color: '#b0b8cc', fontSize: 16, textAlign: 'center', marginBottom: 20 },
  button: {
    backgroundColor: '#e0c060',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 24,
  },
  buttonText: { color: '#1a1a2e', fontWeight: 'bold', fontSize: 16 },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: { color: '#e0c060', fontSize: 16, marginTop: 12 },
});
