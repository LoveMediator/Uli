export function migrateLegacyPersistedState(
  currentKey: string,
  legacyKeys: string[],
): void {
  if (typeof window === 'undefined') {
    return;
  }

  const storage = window.localStorage;
  if (storage.getItem(currentKey) !== null) {
    return;
  }

  for (const legacyKey of legacyKeys) {
    const legacyValue = storage.getItem(legacyKey);
    if (legacyValue === null) {
      continue;
    }

    storage.setItem(currentKey, legacyValue);
    return;
  }
}
