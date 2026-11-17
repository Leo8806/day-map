import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.wordmark}>DAY MAP</Text>
      <Text style={styles.title}>Day Map</Text>
      <StatusBar style="dark" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4EFE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wordmark: {
    fontSize: 12,
    letterSpacing: 1.4,
    color: '#8E867E',
  },
  title: {
    marginTop: 8,
    fontSize: 40,
    color: '#1C1916',
  },
});
