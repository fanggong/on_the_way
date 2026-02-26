import AsyncStorage from '@react-native-async-storage/async-storage';

const PENDING_EXTERNAL_ID_KEY = 'pending_external_id';

function generateExternalId(): string {
  const now = new Date();
  const ts = now.toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
  const suffix = Math.floor(Math.random() * 10000)
    .toString()
    .padStart(4, '0');
  return `ios-${ts}-${suffix}`;
}

export async function getOrCreatePendingExternalId(): Promise<string> {
  const existing = await AsyncStorage.getItem(PENDING_EXTERNAL_ID_KEY);
  if (existing) {
    return existing;
  }

  const created = generateExternalId();
  await AsyncStorage.setItem(PENDING_EXTERNAL_ID_KEY, created);
  return created;
}

export async function clearPendingExternalId(): Promise<void> {
  await AsyncStorage.removeItem(PENDING_EXTERNAL_ID_KEY);
}
