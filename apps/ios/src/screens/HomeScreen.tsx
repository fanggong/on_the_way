import React, {useCallback, useMemo, useRef, useState} from 'react';
import {Animated, Easing, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View} from 'react-native';

import {DEFAULT_THEME_KEY, HOME_THEMES, type ThemeDefinition, type ThemeKey} from '../config/themes';
import ThemeCard from '../components/ThemeCard';
import ThemeNavBar from '../components/ThemeNavBar';
import {tokens} from '../theme/tokens';

type Props = {
  onOpenDebug: () => void;
};

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  }).format(date);
}

export default function HomeScreen({onOpenDebug}: Props) {
  const {width} = useWindowDimensions();
  const [selectedKey, setSelectedKey] = useState<ThemeKey>(DEFAULT_THEME_KEY);
  const [feedbackVisible, setFeedbackVisible] = useState(false);
  const [feedbackText, setFeedbackText] = useState('即将开放');
  const feedbackAnimation = useRef(new Animated.Value(0)).current;

  const todayText = useMemo(() => formatDate(new Date()), []);
  const cardWidth = useMemo(() => {
    const available = width - tokens.spacing.xl * 2 - tokens.spacing.sm;
    return Math.floor(available / 2);
  }, [width]);

  const showComingSoon = useCallback(
    (theme: ThemeDefinition) => {
      setSelectedKey(theme.key);
      setFeedbackText(`${theme.title}即将开放`);
      setFeedbackVisible(true);

      feedbackAnimation.stopAnimation();
      feedbackAnimation.setValue(0);
      Animated.sequence([
        Animated.timing(feedbackAnimation, {
          toValue: 1,
          duration: tokens.motion.fast,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.delay(1200),
        Animated.timing(feedbackAnimation, {
          toValue: 0,
          duration: tokens.motion.standard,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]).start(({finished}) => {
        if (finished) {
          setFeedbackVisible(false);
        }
      });
    },
    [feedbackAnimation],
  );

  const feedbackTranslateY = feedbackAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: [-8, 0],
  });

  return (
    <ScrollView
      style={styles.container}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.content}>
      <Pressable
        onLongPress={onOpenDebug}
        delayLongPress={900}
        accessibilityRole="button"
        accessibilityLabel="首页品牌区，长按进入调试入口"
        style={({pressed}) => [styles.hero, pressed ? styles.heroPressed : null]}>
        <Text style={styles.brand}>On The Way</Text>
        <Text style={styles.subtitle}>今日概览</Text>
        <Text style={styles.date}>{todayText}</Text>
      </Pressable>

      <ThemeNavBar themes={HOME_THEMES} selectedKey={selectedKey} onSelect={showComingSoon} />

      {feedbackVisible ? (
        <Animated.View
          pointerEvents="none"
          style={[
            styles.feedback,
            {
              opacity: feedbackAnimation,
              transform: [{translateY: feedbackTranslateY}],
            },
          ]}>
          <Text style={styles.feedbackText}>{feedbackText}</Text>
        </Animated.View>
      ) : null}

      <View style={styles.grid}>
        {HOME_THEMES.map(item => (
          <ThemeCard
            key={item.key}
            item={item}
            selected={selectedKey === item.key}
            width={cardWidth}
            onPress={showComingSoon}
          />
        ))}
      </View>

      <Text style={styles.footer}>v0.2.0 当前为界面设计版本，更多功能将分阶段开放。</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: tokens.color.bgCanvas,
  },
  content: {
    paddingHorizontal: tokens.spacing.xl,
    paddingTop: tokens.spacing.md,
    paddingBottom: tokens.spacing.xl,
    gap: tokens.spacing.sm,
  },
  hero: {
    backgroundColor: tokens.color.bgSurface,
    borderRadius: tokens.radius.card,
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
    paddingVertical: tokens.spacing.lg,
    paddingHorizontal: tokens.spacing.md,
    gap: 6,
  },
  heroPressed: {
    opacity: 0.92,
  },
  brand: {
    fontSize: tokens.typography.h1,
    lineHeight: tokens.typography.lineHeightH1,
    color: tokens.color.textPrimary,
    fontWeight: '600',
  },
  subtitle: {
    fontSize: tokens.typography.body,
    lineHeight: tokens.typography.lineHeightBody,
    color: tokens.color.textSecondary,
  },
  date: {
    fontSize: tokens.typography.caption,
    lineHeight: tokens.typography.lineHeightCaption,
    color: tokens.color.accentSoft,
    fontWeight: '500',
  },
  feedback: {
    borderRadius: tokens.radius.card,
    borderWidth: 1,
    borderColor: tokens.color.borderDefault,
    backgroundColor: tokens.color.bgCard,
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: tokens.spacing.md,
  },
  feedbackText: {
    color: tokens.color.textPrimary,
    fontSize: tokens.typography.body,
    lineHeight: tokens.typography.lineHeightBody,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: tokens.spacing.sm,
  },
  footer: {
    marginTop: tokens.spacing.xs,
    color: tokens.color.textSecondary,
    fontSize: tokens.typography.caption,
    lineHeight: tokens.typography.lineHeightCaption,
  },
});
