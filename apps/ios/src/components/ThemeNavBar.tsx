import React from 'react';
import {Pressable, ScrollView, StyleSheet, Text} from 'react-native';

import type {ThemeDefinition, ThemeKey} from '../config/themes';
import {tokens} from '../theme/tokens';

type Props = {
  themes: ThemeDefinition[];
  selectedKey: ThemeKey;
  onSelect: (theme: ThemeDefinition) => void;
};

export default function ThemeNavBar({themes, selectedKey, onSelect}: Props) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.container}>
      {themes.map(theme => {
        const selected = selectedKey === theme.key;
        return (
          <Pressable
            key={theme.key}
            accessibilityRole="button"
            accessibilityLabel={`切换主题：${theme.title}`}
            onPress={() => onSelect(theme)}
            style={({pressed}) => [
              styles.tab,
              selected ? styles.tabSelected : null,
              pressed ? styles.tabPressed : null,
            ]}>
            <Text style={[styles.tabText, selected ? styles.tabTextSelected : null]}>{theme.title}</Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: tokens.spacing.sm,
    gap: tokens.spacing.xs,
  },
  tab: {
    minHeight: 44,
    borderRadius: tokens.radius.pill,
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
    paddingHorizontal: tokens.spacing.md,
    justifyContent: 'center',
    backgroundColor: tokens.color.bgCard,
  },
  tabSelected: {
    backgroundColor: tokens.color.bgSurface,
    borderColor: tokens.color.accentSoft,
  },
  tabPressed: {
    opacity: 0.88,
    transform: [{scale: 0.98}],
  },
  tabText: {
    fontSize: tokens.typography.body,
    lineHeight: tokens.typography.lineHeightBody,
    color: tokens.color.textSecondary,
    fontWeight: '500',
  },
  tabTextSelected: {
    color: tokens.color.textPrimary,
    fontWeight: '600',
  },
});
