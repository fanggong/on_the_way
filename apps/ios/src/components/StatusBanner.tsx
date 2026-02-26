import React from 'react';
import {StyleSheet, Text, View} from 'react-native';

import type {SubmitStatus} from '../types/api';

type Props = {
  status: SubmitStatus;
  message?: string;
};

export default function StatusBanner({status, message}: Props) {
  if (status === 'idle') {
    return null;
  }

  return (
    <View style={[styles.container, status === 'error' ? styles.error : styles.success]}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 8,
    marginTop: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  success: {
    backgroundColor: '#d1fae5',
  },
  error: {
    backgroundColor: '#fee2e2',
  },
  text: {
    color: '#111827',
    fontSize: 14,
  },
});
