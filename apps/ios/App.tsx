import React, {useState} from 'react';
import {Pressable, SafeAreaView, StyleSheet, Text, View} from 'react-native';

import DailySummaryScreen from './src/screens/DailySummaryScreen';
import HomeScreen from './src/screens/HomeScreen';
import ManualInputScreen from './src/screens/ManualInputScreen';
import {tokens} from './src/theme/tokens';

type Route = 'home' | 'manual' | 'summary';

export default function App() {
  const [route, setRoute] = useState<Route>('home');

  if (route === 'home') {
    return <HomeScreen onOpenDebug={() => setRoute('manual')} />;
  }

  const title = route === 'manual' ? '调试录入' : '调试查询';

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{title}</Text>
        <View style={styles.tabRow}>
          <Pressable
            style={({pressed}) => [styles.tab, pressed ? styles.tabPressed : null]}
            onPress={() => setRoute('home')}>
            <Text style={styles.tabText}>首页</Text>
          </Pressable>

          <Pressable
            style={({pressed}) => [
              styles.tab,
              route === 'manual' ? styles.tabActive : null,
              pressed ? styles.tabPressed : null,
            ]}
            onPress={() => setRoute('manual')}>
            <Text style={[styles.tabText, route === 'manual' ? styles.tabTextActive : null]}>手工录入</Text>
          </Pressable>

          <Pressable
            style={({pressed}) => [
              styles.tab,
              route === 'summary' ? styles.tabActive : null,
              pressed ? styles.tabPressed : null,
            ]}
            onPress={() => setRoute('summary')}>
            <Text style={[styles.tabText, route === 'summary' ? styles.tabTextActive : null]}>结果查看</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.body}>{route === 'manual' ? <ManualInputScreen /> : <DailySummaryScreen />}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: tokens.color.bgCanvas,
  },
  header: {
    paddingHorizontal: tokens.spacing.md,
    paddingTop: tokens.spacing.xs,
    paddingBottom: 10,
    backgroundColor: tokens.color.bgSurface,
    borderBottomWidth: 1,
    borderBottomColor: tokens.color.borderDefault,
  },
  headerTitle: {
    color: tokens.color.textPrimary,
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  tabRow: {
    flexDirection: 'row',
    gap: tokens.spacing.xs,
  },
  tab: {
    backgroundColor: tokens.color.bgCard,
    borderRadius: tokens.radius.pill,
    paddingHorizontal: tokens.spacing.sm,
    minHeight: 40,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
  },
  tabActive: {
    backgroundColor: tokens.color.bgSurface,
    borderColor: tokens.color.accentSoft,
  },
  tabPressed: {
    opacity: 0.88,
    transform: [{scale: 0.98}],
  },
  tabText: {
    color: tokens.color.textSecondary,
    fontWeight: '500',
    fontSize: tokens.typography.caption,
  },
  tabTextActive: {
    color: tokens.color.textPrimary,
    fontWeight: '600',
  },
  body: {
    flex: 1,
  },
});
