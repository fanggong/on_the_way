import React from 'react';
import {StyleSheet, View} from 'react-native';

import type {ThemeKey} from '../config/themes';

type Props = {
  themeKey: ThemeKey;
  color: string;
  size?: number;
};

function HealthIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.circle, {borderColor: color}]} />
      <View style={[styles.crossHorizontal, {backgroundColor: color}]} />
      <View style={[styles.crossVertical, {backgroundColor: color}]} />
    </>
  );
}

function TimeIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.circle, {borderColor: color}]} />
      <View style={[styles.clockHandShort, {backgroundColor: color}]} />
      <View style={[styles.clockHandLong, {backgroundColor: color}]} />
      <View style={[styles.clockCenter, {backgroundColor: color}]} />
    </>
  );
}

function IncomeIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.chartBaseline, {backgroundColor: color}]} />
      <View style={[styles.chartDiagA, {backgroundColor: color}]} />
      <View style={[styles.chartDiagB, {backgroundColor: color}]} />
      <View style={[styles.chartArrowA, {backgroundColor: color}]} />
      <View style={[styles.chartArrowB, {backgroundColor: color}]} />
    </>
  );
}

function FinanceIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.walletBody, {borderColor: color}]} />
      <View style={[styles.walletFlap, {backgroundColor: color}]} />
      <View style={[styles.walletDot, {backgroundColor: color}]} />
    </>
  );
}

function CapabilityIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.bookLeft, {borderColor: color}]} />
      <View style={[styles.bookRight, {borderColor: color}]} />
      <View style={[styles.bookCenter, {backgroundColor: color}]} />
    </>
  );
}

function RelationshipIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.linkCircleLeft, {borderColor: color}]} />
      <View style={[styles.linkCircleRight, {borderColor: color}]} />
      <View style={[styles.linkBridge, {backgroundColor: color}]} />
    </>
  );
}

function LifestyleIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.homeRoofA, {backgroundColor: color}]} />
      <View style={[styles.homeRoofB, {backgroundColor: color}]} />
      <View style={[styles.homeBody, {borderColor: color}]} />
      <View style={[styles.homeDoor, {backgroundColor: color}]} />
    </>
  );
}

function SecurityIcon({color}: {color: string}) {
  return (
    <>
      <View style={[styles.lockBody, {borderColor: color}]} />
      <View style={[styles.lockShackle, {borderColor: color}]} />
      <View style={[styles.lockKeyhole, {backgroundColor: color}]} />
    </>
  );
}

export default function ThemeIcon({themeKey, color, size = 24}: Props) {
  const scale = size / 24;

  return (
    <View style={[styles.wrapper, {width: size, height: size}]}>
      <View style={[styles.canvas, {transform: [{scale}]}]}>
        {themeKey === 'health' ? <HealthIcon color={color} /> : null}
        {themeKey === 'time' ? <TimeIcon color={color} /> : null}
        {themeKey === 'income' ? <IncomeIcon color={color} /> : null}
        {themeKey === 'finance' ? <FinanceIcon color={color} /> : null}
        {themeKey === 'capability' ? <CapabilityIcon color={color} /> : null}
        {themeKey === 'relationship' ? <RelationshipIcon color={color} /> : null}
        {themeKey === 'lifestyle' ? <LifestyleIcon color={color} /> : null}
        {themeKey === 'security' ? <SecurityIcon color={color} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  canvas: {
    width: 24,
    height: 24,
    position: 'relative',
  },
  circle: {
    position: 'absolute',
    top: 2,
    left: 2,
    width: 20,
    height: 20,
    borderWidth: 1.8,
    borderRadius: 10,
  },
  crossHorizontal: {
    position: 'absolute',
    top: 11,
    left: 7,
    width: 10,
    height: 1.8,
    borderRadius: 999,
  },
  crossVertical: {
    position: 'absolute',
    top: 7,
    left: 11,
    width: 1.8,
    height: 10,
    borderRadius: 999,
  },
  clockHandShort: {
    position: 'absolute',
    top: 8,
    left: 11,
    width: 1.8,
    height: 6,
    borderRadius: 999,
  },
  clockHandLong: {
    position: 'absolute',
    top: 11,
    left: 11,
    width: 6,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '30deg'}],
  },
  clockCenter: {
    position: 'absolute',
    top: 10.4,
    left: 10.4,
    width: 3.2,
    height: 3.2,
    borderRadius: 2,
  },
  chartBaseline: {
    position: 'absolute',
    bottom: 4,
    left: 3,
    width: 18,
    height: 1.8,
    borderRadius: 999,
  },
  chartDiagA: {
    position: 'absolute',
    bottom: 7,
    left: 6,
    width: 8,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '-35deg'}],
  },
  chartDiagB: {
    position: 'absolute',
    bottom: 11,
    left: 12.5,
    width: 7,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '15deg'}],
  },
  chartArrowA: {
    position: 'absolute',
    top: 4.8,
    right: 4.2,
    width: 4.8,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '-38deg'}],
  },
  chartArrowB: {
    position: 'absolute',
    top: 7.8,
    right: 4.2,
    width: 4.8,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '38deg'}],
  },
  walletBody: {
    position: 'absolute',
    top: 6,
    left: 3,
    width: 18,
    height: 13,
    borderWidth: 1.8,
    borderRadius: 4,
  },
  walletFlap: {
    position: 'absolute',
    top: 10.5,
    left: 4.5,
    width: 15,
    height: 1.8,
    borderRadius: 999,
  },
  walletDot: {
    position: 'absolute',
    top: 10,
    right: 6.8,
    width: 2.8,
    height: 2.8,
    borderRadius: 2,
  },
  bookLeft: {
    position: 'absolute',
    top: 5,
    left: 3,
    width: 9,
    height: 14,
    borderWidth: 1.8,
    borderTopLeftRadius: 4,
    borderBottomLeftRadius: 4,
    borderTopRightRadius: 2,
    borderBottomRightRadius: 2,
  },
  bookRight: {
    position: 'absolute',
    top: 5,
    right: 3,
    width: 9,
    height: 14,
    borderWidth: 1.8,
    borderTopRightRadius: 4,
    borderBottomRightRadius: 4,
    borderTopLeftRadius: 2,
    borderBottomLeftRadius: 2,
  },
  bookCenter: {
    position: 'absolute',
    top: 5.8,
    left: 11.1,
    width: 1.8,
    height: 12.2,
    borderRadius: 999,
  },
  linkCircleLeft: {
    position: 'absolute',
    top: 6,
    left: 2.8,
    width: 10,
    height: 10,
    borderWidth: 1.8,
    borderRadius: 5,
  },
  linkCircleRight: {
    position: 'absolute',
    top: 8,
    right: 2.8,
    width: 10,
    height: 10,
    borderWidth: 1.8,
    borderRadius: 5,
  },
  linkBridge: {
    position: 'absolute',
    top: 11.2,
    left: 9,
    width: 6,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '18deg'}],
  },
  homeRoofA: {
    position: 'absolute',
    top: 6.6,
    left: 5.2,
    width: 8,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '-35deg'}],
  },
  homeRoofB: {
    position: 'absolute',
    top: 6.6,
    right: 5.2,
    width: 8,
    height: 1.8,
    borderRadius: 999,
    transform: [{rotate: '35deg'}],
  },
  homeBody: {
    position: 'absolute',
    top: 11,
    left: 5.2,
    width: 13.6,
    height: 9,
    borderWidth: 1.8,
    borderRadius: 2,
  },
  homeDoor: {
    position: 'absolute',
    top: 13.5,
    left: 11,
    width: 2,
    height: 6.5,
    borderRadius: 999,
  },
  lockBody: {
    position: 'absolute',
    top: 10,
    left: 5,
    width: 14,
    height: 10,
    borderWidth: 1.8,
    borderRadius: 3,
  },
  lockShackle: {
    position: 'absolute',
    top: 4,
    left: 7.5,
    width: 9,
    height: 8,
    borderWidth: 1.8,
    borderBottomWidth: 0,
    borderTopLeftRadius: 5,
    borderTopRightRadius: 5,
  },
  lockKeyhole: {
    position: 'absolute',
    top: 13.4,
    left: 11,
    width: 2,
    height: 3.4,
    borderRadius: 999,
  },
});
