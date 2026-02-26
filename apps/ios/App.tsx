import React, {useState} from 'react';
import {SafeAreaView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';

import DailySummaryScreen from './src/screens/DailySummaryScreen';
import ManualInputScreen from './src/screens/ManualInputScreen';

type Tab = 'manual' | 'summary';

export default function App() {
  const [tab, setTab] = useState<Tab>('manual');

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>On The Way v0.1.0</Text>
        <View style={styles.tabRow}>
          <TouchableOpacity
            style={[styles.tab, tab === 'manual' ? styles.tabActive : null]}
            onPress={() => setTab('manual')}>
            <Text style={styles.tabText}>手工录入</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, tab === 'summary' ? styles.tabActive : null]}
            onPress={() => setTab('summary')}>
            <Text style={styles.tabText}>结果查看</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.body}>{tab === 'manual' ? <ManualInputScreen /> : <DailySummaryScreen />}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#e5e7eb',
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 10,
    backgroundColor: '#111827',
  },
  headerTitle: {
    color: '#f9fafb',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 10,
  },
  tabRow: {
    flexDirection: 'row',
    gap: 8,
  },
  tab: {
    backgroundColor: '#374151',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  tabActive: {
    backgroundColor: '#059669',
  },
  tabText: {
    color: '#f9fafb',
    fontWeight: '600',
  },
  body: {
    flex: 1,
  },
});
