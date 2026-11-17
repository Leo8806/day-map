import { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { categories, events, type Category } from '../data';
import { colors } from '../theme';

const DAY_START = 8;
const DAY_END = 21;

export function FiltersSheet({
  visible,
  category,
  startHour,
  endHour,
  onCategory,
  onHours,
  onReset,
  onClose,
}: {
  visible: boolean;
  category: Category | null;
  startHour: number;
  endHour: number;
  onCategory: (category: Category | null) => void;
  onHours: (startHour: number, endHour: number) => void;
  onReset: () => void;
  onClose: () => void;
}) {
  const count = events.filter((event) => {
    const inCategory = category == null || event.category === category;
    return inCategory && event.startHour >= startHour && event.startHour < endHour;
  }).length;

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <Pressable style={styles.dismiss} onPress={onClose} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.heading}>
            <View style={styles.headingCopy}>
              <Text style={styles.kicker}>MAKE THE GAPS YOURS</Text>
              <Text style={styles.title}>Filters & interests</Text>
              <Text style={styles.sub}>A few things worth making time for.</Text>
            </View>
            <Pressable onPress={onClose} style={styles.close}>
              <Text style={styles.closeMark}>×</Text>
            </Pressable>
          </View>

          <Text style={styles.section}>Select categories</Text>
          <View style={styles.pills}>
            {categories.map((item) => {
              const on = item === category;
              return (
                <Pressable key={item} onPress={() => onCategory(on ? null : item)} style={[styles.pill, on && styles.pillOn]}>
                  <Text style={[styles.pillText, on && styles.pillTextOn]}>{item}</Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={styles.section}>Available time today</Text>
          <Text style={styles.range}>
            {formatHour(startHour)} – {formatHour(endHour)}
          </Text>
          <RangeSlider startHour={startHour} endHour={endHour} onChange={onHours} />

          <View style={styles.actions}>
            <Pressable onPress={onReset}>
              <Text style={styles.reset}>Reset</Text>
            </Pressable>
            <Pressable onPress={onClose} style={styles.show}>
              <Text style={styles.showText}>Show {count} events</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function RangeSlider({
  startHour,
  endHour,
  onChange,
}: {
  startHour: number;
  endHour: number;
  onChange: (startHour: number, endHour: number) => void;
}) {
  const [width, setWidth] = useState(1);

  function move(x: number) {
    const ratio = Math.min(1, Math.max(0, x / width));
    const hour = Math.round(DAY_START + ratio * (DAY_END - DAY_START));
    if (Math.abs(hour - startHour) <= Math.abs(hour - endHour)) {
      onChange(Math.min(hour, endHour - 1), endHour);
    } else {
      onChange(startHour, Math.max(hour, startHour + 1));
    }
  }

  const startPct = ((startHour - DAY_START) / (DAY_END - DAY_START)) * 100;
  const endPct = ((endHour - DAY_START) / (DAY_END - DAY_START)) * 100;

  return (
    <View
      style={styles.slider}
      onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
      onStartShouldSetResponder={() => true}
      onMoveShouldSetResponder={() => true}
      onResponderGrant={(event) => move(event.nativeEvent.locationX)}
      onResponderMove={(event) => move(event.nativeEvent.locationX)}
    >
      <View style={styles.track} />
      <View style={[styles.fill, { left: `${startPct}%`, width: `${endPct - startPct}%` }]} />
      <View style={[styles.knob, { left: `${startPct}%` }]} />
      <View style={[styles.knob, { left: `${endPct}%` }]} />
      <View style={styles.scale}>
        <Text style={styles.scaleText}>{formatHour(DAY_START)}</Text>
        <Text style={styles.scaleText}>{formatHour(DAY_END)}</Text>
      </View>
    </View>
  );
}

function formatHour(hour: number) {
  const suffix = hour >= 12 ? 'PM' : 'AM';
  const face = hour % 12 === 0 ? 12 : hour % 12;
  return `${face} ${suffix}`;
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: colors.overlay },
  dismiss: { flex: 1 },
  sheet: {
    backgroundColor: colors.bg,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 24,
  },
  handle: { alignSelf: 'center', width: 42, height: 4, borderRadius: 2, backgroundColor: colors.line, marginBottom: 14 },
  heading: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  headingCopy: { flex: 1 },
  kicker: { letterSpacing: 0.8, fontSize: 11, color: colors.muted },
  title: { marginTop: 4, fontSize: 28, color: colors.ink, fontFamily: 'Georgia' },
  sub: { marginTop: 4, color: colors.muted },
  close: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeMark: { fontSize: 22, color: colors.ink, marginTop: -2 },
  section: { marginTop: 18, fontSize: 16, color: colors.ink },
  pills: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  pill: { borderWidth: 1.5, borderColor: colors.ink, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 7, backgroundColor: colors.white },
  pillOn: { backgroundColor: colors.black, borderColor: colors.black },
  pillText: { color: colors.ink },
  pillTextOn: { color: colors.white },
  range: { marginTop: 6, fontSize: 28, color: colors.ink, fontFamily: 'Georgia' },
  slider: { marginTop: 16, height: 54, justifyContent: 'center' },
  track: { height: 3, backgroundColor: colors.line, borderRadius: 2 },
  fill: { position: 'absolute', top: 25, height: 3, backgroundColor: colors.orange },
  knob: {
    position: 'absolute',
    top: 16,
    width: 20,
    height: 20,
    marginLeft: -10,
    borderRadius: 10,
    backgroundColor: colors.white,
    borderWidth: 2,
    borderColor: colors.ink,
  },
  scale: { position: 'absolute', left: 0, right: 0, bottom: 0, flexDirection: 'row', justifyContent: 'space-between' },
  scaleText: { color: colors.muted, fontSize: 12 },
  actions: { marginTop: 18, flexDirection: 'row', alignItems: 'center', gap: 16 },
  reset: { color: colors.ink, textDecorationLine: 'underline', fontSize: 16 },
  show: {
    flex: 1,
    backgroundColor: colors.orange,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.ink,
    paddingVertical: 14,
    alignItems: 'center',
  },
  showText: { color: colors.white, fontSize: 16 },
});
