import React, { useMemo, useState, useRef } from 'react';
import { ActivityIndicator, FlatList, ImageBackground, SafeAreaView, StyleSheet, Text, TouchableOpacity, View, Dimensions, Image } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImageManipulator from 'expo-image-manipulator';
import { StatusBar } from 'expo-status-bar';

const HERO_IMAGE = require('./assets/hero.png');
const API_BASE_URL = 'http://192.168.1.11:8000';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GUIDE_SIZE = SCREEN_WIDTH * 0.8; 

export default function App() {
  const [screen, setScreen] = useState('home');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);

  const totalCrowns = useMemo(() => {
    if (!result?.tiles) return 0;
    return result.tiles.reduce((sum, t) => sum + t.crowns, 0);
  }, [result]);

  const handleStartCamera = async () => {
    if (!permission?.granted) {
      const p = await requestPermission();
      if (!p.granted) {
        setError('Kamera-tilladelse blev ikke givet.');
        return;
      }
    }
    setScreen('camera');
  };

  const handleTakePicture = async () => {
    if (!cameraRef.current) return;
    setLoading(true);

    try {
      // 1. Tag billede i hÃ¸jeste kvalitet
      const photo = await cameraRef.current.takePictureAsync({
        quality: 1,
        base64: false,
      });

      setScreen('loading');

      // 2. BeskÃ¦ring og reskalering
      // Billedet fra kameraet har photo.width og photo.height.
      // Den udgÃ¸r typisk et skÃ¦rm-format (f.eks. 16:9 eller 4:3).
      // Vores guide er kvadratisk i midten af skÃ¦rmen.
      const imageWidth = photo.width;
      const imageHeight = photo.height;
      
      const shortSide = Math.min(imageWidth, imageHeight);
      // Vi tager en firkant ud fra midten af centeret (hvor guiden er)
      const cropSize = shortSide * 0.8; // Samme procent som GUIDE_SIZE pa skÃ¦rmen
      
      const cropAction = {
        crop: {
          originX: (imageWidth - cropSize) / 2,
          originY: (imageHeight - cropSize) / 2,
          width: cropSize,
          height: cropSize,
        }
      };

      const resizeAction = {
        resize: { width: 500, height: 500 }
      };

      const manipulated = await ImageManipulator.manipulateAsync(
        photo.uri,
        [cropAction, resizeAction],
        { compress: 0.9, format: ImageManipulator.SaveFormat.JPEG }
      );

      // 3. Send til backend
      const uri = manipulated.uri;
      const filename = uri.split('/').pop() || 'board.jpg';
      
      const formData = new FormData();
      formData.append('file', {
        uri,
        name: filename,
        type: 'image/jpeg',
      });

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        const msg = await response.text();
        throw new Error(msg || 'Ukendt fejl fra backend.');
      }

      const data = await response.json();
      data.resultImageUri = uri; // Gem den beskÃ¥rne uri for at vise den!
      setResult(data);

      setHistory((prev) => [
        {
          id: `${Date.now()}`,
          tidspunkt: new Date().toLocaleTimeString('da-DK'),
          score: data.total_score,
          crowns: (data.tiles || []).reduce((sum, t) => sum + t.crowns, 0),
        },
        ...prev,
      ]);

      setScreen('result');
    } catch (e) {
      setError(`Analyse fejlede: ${String(e.message || e)}`);
      setScreen('home');
    } finally {
      setLoading(false);
    }
  };

  if (screen === 'loading') {
    return (
      <ImageBackground source={HERO_IMAGE} style={styles.hero} imageStyle={styles.heroImage}>
        <View style={styles.overlayCenter}>
          <ActivityIndicator size="large" color="#ffd166" />
          <Text style={styles.loadingText}>Analyserer pladen...</Text>
        </View>
        <StatusBar style="light" />
      </ImageBackground>
    );
  }

  if (screen === 'camera') {
    return (
      <View style={styles.cameraContainer}>
        <CameraView style={styles.camera} ref={cameraRef} facing="back" />
        <View style={[styles.maskContainer, StyleSheet.absoluteFill]}>
          <View style={styles.maskTop} />
          <View style={styles.maskCenterRow}>
            <View style={styles.maskSide} />
            <View style={styles.guideHole}>
              <View style={styles.cornerTL} /><View style={styles.cornerTR} />
              <View style={styles.cornerBL} /><View style={styles.cornerBR} />
            </View>
            <View style={styles.maskSide} />
          </View>
          <View style={styles.maskBottom}>
            <TouchableOpacity style={styles.captureBtn} onPress={handleTakePicture} disabled={loading}>
                <View style={styles.captureBtnInner} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelBtn} onPress={() => setScreen('home')}>
              <Text style={styles.btnText}>Annuller</Text>
            </TouchableOpacity>
          </View>
        </View>
        <StatusBar style="light" />
      </View>
    );
  }

  if (screen === 'result') {
    // 500 px fra backend svarer til vores screen element size
    const RESULT_IMAGE_SIZE = Dimensions.get('window').width - 48; // Padding
    const scale = RESULT_IMAGE_SIZE / 500;

    return (
      <View style={styles.resultRoot}>
        <StatusBar style="dark" />
        
        <View style={styles.imageOverlayContainer}>
          <Image source={{ uri: result?.resultImageUri }} style={{ width: RESULT_IMAGE_SIZE, height: RESULT_IMAGE_SIZE, borderRadius: 8 }} />
          
          {/* Tegn clusters overlay */}
          {result?.clusters?.map((c, i) => {
            const colors = ['rgba(255,0,0,0.3)', 'rgba(0,255,0,0.3)', 'rgba(0,0,255,0.3)', 'rgba(255,255,0,0.3)', 'rgba(255,0,255,0.3)', 'rgba(0,255,255,0.3)'];
            const color = colors[i % colors.length];
            return c.coordinates?.map(([cx, cy], j) => (
              <View key={'c-' + i + '-' + j} style={{
                position: 'absolute',
                left: cx * 100 * scale,
                top: cy * 100 * scale,
                width: 100 * scale,
                height: 100 * scale,
                backgroundColor: color,
                borderWidth: 1,
                borderColor: 'rgba(255,255,255,0.5)'
              }} />
            ));
          })}
          
          {/* Tegn kroner */}
          {result?.crown_boxes?.map((box, i) => (
            <View key={`crown-${i}`} style={{
              position: 'absolute',
              left: box.x * scale,
              top: box.y * scale,
              width: box.w * scale,
              height: box.h * scale,
              borderWidth: 2,
              borderColor: '#0f0', // GrÃ¸n boks om kronen
              backgroundColor: 'rgba(0,255,0,0.2)'
            }} />
          ))}
        </View>

        <View style={styles.resultCard}>
          <Text style={styles.title}>Resultat: {result?.total_score ?? '-'}</Text>
          <Text style={styles.meta}>Kroner fundet: {totalCrowns}</Text>
          <Text style={styles.meta}>Clusters: {result?.clusters?.length ?? 0}</Text>
        </View>

        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.primaryBtn} onPress={() => setScreen('camera')}>
            <Text style={styles.btnText}>Ny scannig</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryBtn} onPress={() => setScreen('home')}>
            <Text style={styles.btnText}>Til forside</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ImageBackground source={HERO_IMAGE} style={styles.hero} imageStyle={styles.heroImage}>
      <View style={styles.overlayCenter}>
        <Text style={styles.appTitle}>Kingdomino</Text>
        <Text style={styles.subtitleCenter}>Placer pladen i rammen, og fÃ¥ scoret brÃ¦ttet med det samme.</Text>

        {!!error && <Text style={styles.errorText}>{error}</Text>}

        <TouchableOpacity style={styles.primaryBtn} onPress={handleStartCamera} disabled={loading}>
          <Text style={styles.btnText}>Start Kamera</Text>
        </TouchableOpacity>
      </View>
      <StatusBar style="light" />
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  hero: { flex: 1 },
  heroImage: { resizeMode: 'cover' },
  overlayCenter: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    gap: 16,
  },
  appTitle: { fontSize: 40, fontWeight: '900', color: '#fff' },
  subtitleCenter: { fontSize: 16, color: '#ddd', textAlign: 'center', marginBottom: 20 },
  loadingText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  errorText: { color: '#ff4444', backgroundColor: '#fff', padding: 8, borderRadius: 8 },
  primaryBtn: { backgroundColor: '#ffd166', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 12 },
  secondaryBtn: { backgroundColor: 'rgba(255,255,255,0.2)', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 12 },
  btnText: { fontSize: 18, fontWeight: 'bold', color: '#111' },
  
  // Camera styles
  cameraContainer: { flex: 1, backgroundColor: '#000' },
  camera: { flex: 1 },
  maskContainer: { flex: 1 },
  maskTop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  maskBottom: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', alignItems: 'center', justifyContent: 'center', gap: 20 },
  maskCenterRow: { flexDirection: 'row', height: GUIDE_SIZE },
  maskSide: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  guideHole: { width: GUIDE_SIZE, height: GUIDE_SIZE, borderColor: 'rgba(255,255,255,0.3)', borderWidth: 2, backgroundColor: 'transparent' },
  
  // Corner markers
  cornerTL: { position: 'absolute', top: -2, left: -2, width: 30, height: 30, borderColor: '#ffd166', borderTopWidth: 4, borderLeftWidth: 4 },
  cornerTR: { position: 'absolute', top: -2, right: -2, width: 30, height: 30, borderColor: '#ffd166', borderTopWidth: 4, borderRightWidth: 4 },
  cornerBL: { position: 'absolute', bottom: -2, left: -2, width: 30, height: 30, borderColor: '#ffd166', borderBottomWidth: 4, borderLeftWidth: 4 },
  cornerBR: { position: 'absolute', bottom: -2, right: -2, width: 30, height: 30, borderColor: '#ffd166', borderBottomWidth: 4, borderRightWidth: 4 },

  captureBtn: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.3)', justifyContent: 'center', alignItems: 'center' },
  captureBtnInner: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#fff' },
  cancelBtn: { padding: 10 },
  
  // Result styles
  resultRoot: { flex: 1, backgroundColor: '#f8f9fa', alignItems: 'center', paddingTop: 60, paddingHorizontal: 24 },
  imageOverlayContainer: { backgroundColor: '#fff', borderRadius: 8, elevation: 4, shadowColor: '#000', shadowOpacity: 0.1, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, overflow: 'hidden' },
  resultCard: { width: '100%', backgroundColor: '#fff', padding: 20, borderRadius: 16, marginTop: 24, gap: 8, elevation: 2, shadowColor: '#000', shadowOpacity: 0.05, shadowOffset: { width: 0, height: 2 } },
  title: { fontSize: 24, fontWeight: 'bold' },
  meta: { fontSize: 16, color: '#555' },
  buttonRow: { flexDirection: 'row', gap: 16, marginTop: 'auto', marginBottom: 40 },
});
