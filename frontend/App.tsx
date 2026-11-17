import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from './src/theme';

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
    backgroundColor: colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wordmark: {
    fontSize: 12,
    letterSpacing: 1.4,
    color: colors.muted,
  },
  title: {
    marginTop: 8,
    fontSize: 40,
    color: colors.ink,
  },
});
