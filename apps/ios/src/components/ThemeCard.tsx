import React from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ThemeDefinition} from '../config/themes';
import {tokens} from '../theme/tokens';
import ThemeIcon from './ThemeIcon';

type Props = {
  item: ThemeDefinition;
  selected: boolean;
  width: number;
  onPress: (item: ThemeDefinition) => void;
};

export default function ThemeCard({item, selected, width, onPress}: Props) {
  const iconColor = selected ? tokens.color.textPrimary : tokens.color.accentSoft;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${item.title}，${item.description}`}
      onPress={() => onPress(item)}
      style={({pressed}) => [
        styles.card,
        {width},
        selected ? styles.cardSelected : null,
        pressed ? styles.cardPressed : null,
      ]}>
      <View style={styles.headerRow}>
        <ThemeIcon themeKey={item.key} color={iconColor} size={24} />
        <Text style={[styles.title, selected ? styles.titleSelected : null]} numberOfLines={1}>
          {item.title}
        </Text>
      </View>

      <Text style={styles.description} numberOfLines={2}>
        {item.description}
      </Text>

      <View style={styles.statusBadge}>
        <Text style={styles.statusText}>{item.statusText}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 150,
    backgroundColor: tokens.color.bgCard,
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
    borderRadius: tokens.radius.card,
    padding: tokens.spacing.md,
    gap: tokens.spacing.sm,
  },
  cardSelected: {
    backgroundColor: tokens.color.bgSurface,
    borderColor: tokens.color.accentSoft,
  },
  cardPressed: {
    opacity: 0.9,
    transform: [{scale: 0.98}],
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.spacing.xs,
  },
  title: {
    flexShrink: 1,
    fontSize: tokens.typography.h2,
    lineHeight: tokens.typography.lineHeightH2,
    color: tokens.color.textPrimary,
    fontWeight: '600',
  },
  titleSelected: {
    color: tokens.color.textPrimary,
  },
  description: {
    fontSize: tokens.typography.body,
    lineHeight: tokens.typography.lineHeightBody,
    color: tokens.color.textSecondary,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    borderRadius: tokens.radius.pill,
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
    paddingHorizontal: tokens.spacing.sm,
    paddingVertical: 6,
    backgroundColor: tokens.color.bgCanvas,
    minHeight: 28,
    justifyContent: 'center',
  },
  statusText: {
    fontSize: tokens.typography.caption,
    lineHeight: tokens.typography.lineHeightCaption,
    color: tokens.color.stateDisabled,
    fontWeight: '500',
  },
});
