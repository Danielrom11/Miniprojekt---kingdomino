import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import heroImage from '../assets/hero.png';

export default function HomeScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Image source={heroImage} style={styles.hero} resizeMode="contain" />
      <Text style={styles.title}>King Domino{'\n'}Points Calculator</Text>
      <Text style={styles.subtitle}>
        Take a photo of your finished game board to calculate your score automatically.
      </Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('Camera')}
        activeOpacity={0.85}
      >
        <Text style={styles.buttonText}>📷  Calculate</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  hero: {
    width: 240,
    height: 240,
    marginBottom: 28,
    borderRadius: 120,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#e0c060',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 36,
  },
  subtitle: {
    fontSize: 15,
    color: '#b0b8cc',
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 22,
  },
  button: {
    backgroundColor: '#e0c060',
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 30,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
});
