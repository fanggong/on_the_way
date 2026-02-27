import React from 'react';
import {SafeAreaView, StyleSheet} from 'react-native';

import HomeScreen from './src/screens/HomeScreen';
import {tokens} from './src/theme/tokens';

export default function App() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <HomeScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: tokens.color.bgCanvas,
  },
});
