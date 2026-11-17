import { StatusBar } from 'expo-status-bar';

import { MapScreen } from './src/components/MapScreen';
import { colors } from './src/theme';

export default function App() {
  return (
    <>
      <StatusBar style="dark" backgroundColor={colors.bg} />
      <MapScreen />
    </>
  );
}
