import React, {useState} from 'react';
import {Button, StyleSheet, Text, TextInput, View} from 'react-native';

import {fetchDailySummary} from '../api/client';
import type {DailySummary} from '../types/api';

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function DailySummaryScreen() {
  const [date, setDate] = useState(today());
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [error, setError] = useState<string>('');

  const onLoad = async () => {
    try {
      setError('');
      const data = await fetchDailySummary(date);
      setSummary(data);
    } catch (e) {
      const err = e as Error;
      setError(err.message);
      setSummary(null);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Daily Summary</Text>

      <Text style={styles.label}>date (YYYY-MM-DD)</Text>
      <TextInput style={styles.input} value={date} onChangeText={setDate} />

      <Button title="查询" onPress={onLoad} />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {summary ? (
        <View style={styles.card}>
          <Text style={styles.item}>stat_date: {summary.stat_date}</Text>
          <Text style={styles.item}>event_count: {summary.event_count}</Text>
          <Text style={styles.item}>manual_count: {summary.manual_count}</Text>
          <Text style={styles.item}>connector_count: {summary.connector_count}</Text>
          <Text style={styles.item}>avg_value: {summary.avg_value}</Text>
          <Text style={styles.item}>min_value: {summary.min_value}</Text>
          <Text style={styles.item}>max_value: {summary.max_value}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f9fafb',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 16,
    color: '#111827',
  },
  label: {
    fontSize: 13,
    color: '#374151',
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#ffffff',
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 12,
  },
  card: {
    marginTop: 16,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    gap: 4,
  },
  item: {
    color: '#111827',
    fontSize: 14,
  },
  error: {
    marginTop: 12,
    color: '#b91c1c',
  },
});
