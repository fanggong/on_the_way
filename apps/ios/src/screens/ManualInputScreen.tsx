import React, {useMemo, useState} from 'react';
import {Button, StyleSheet, Text, TextInput, View} from 'react-native';

import {ingestManualSignal} from '../api/client';
import StatusBanner from '../components/StatusBanner';
import type {SubmitStatus} from '../types/api';
import {clearPendingExternalId, getOrCreatePendingExternalId} from '../utils/externalId';

function getDefaultOccurredAt(): string {
  return new Date().toISOString();
}

function validate(valueRaw: string, occurredAtRaw: string): {ok: true; value: number; occurredAt: string} | {ok: false; message: string} {
  const value = Number(valueRaw);
  if (Number.isNaN(value) || value < 0 || value > 100) {
    return {ok: false, message: 'value 必须是 0-100 的数字'};
  }

  const occurredAt = new Date(occurredAtRaw);
  if (Number.isNaN(occurredAt.getTime())) {
    return {ok: false, message: 'occurred_at 不是合法时间'};
  }

  const maxAllowed = Date.now() + 5 * 60 * 1000;
  if (occurredAt.getTime() > maxAllowed) {
    return {ok: false, message: 'occurred_at 不能晚于当前时间 +5 分钟'};
  }

  return {ok: true, value, occurredAt: occurredAt.toISOString()};
}

export default function ManualInputScreen() {
  const [value, setValue] = useState('');
  const [occurredAt, setOccurredAt] = useState(getDefaultOccurredAt());
  const [note, setNote] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [message, setMessage] = useState('');

  const isSubmitting = useMemo(() => status === 'submitting', [status]);

  const onSubmit = async () => {
    const validated = validate(value, occurredAt);
    if (!validated.ok) {
      setStatus('error');
      setMessage(validated.message);
      return;
    }

    setStatus('submitting');
    setMessage('提交中...');

    try {
      const externalId = await getOrCreatePendingExternalId();
      const result = await ingestManualSignal({
        source_id: 'ios_manual',
        external_id: externalId,
        occurred_at: validated.occurredAt,
        payload: {
          value: validated.value,
          note: note || undefined,
        },
      });

      await clearPendingExternalId();
      setStatus('success');
      setMessage(`提交成功，raw_id=${result.raw_id}，idempotent=${result.idempotent}`);
    } catch (error) {
      const err = error as Error;
      setStatus('error');
      if (err.message.includes('INVALID_ARGUMENT')) {
        setMessage(`参数错误: ${err.message}`);
      } else {
        setMessage(`服务不可用或提交失败: ${err.message}`);
      }
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>手工录入 Signal</Text>

      <Text style={styles.label}>value (0-100)</Text>
      <TextInput
        keyboardType="decimal-pad"
        style={styles.input}
        value={value}
        onChangeText={setValue}
        placeholder="例如 73.5"
      />

      <Text style={styles.label}>occurred_at (ISO-8601)</Text>
      <TextInput
        style={styles.input}
        value={occurredAt}
        onChangeText={setOccurredAt}
        placeholder="2026-02-25T10:30:00Z"
      />

      <Text style={styles.label}>note (optional)</Text>
      <TextInput
        style={styles.input}
        value={note}
        onChangeText={setNote}
        placeholder="manual input from ios"
      />

      <Button title={isSubmitting ? '提交中...' : '提交'} onPress={onSubmit} disabled={isSubmitting} />

      <StatusBanner status={status} message={message} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
    padding: 16,
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
    marginTop: 12,
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#ffffff',
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
});
