import { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { alternatives, type Alternative } from '../data';
import { colors } from '../theme';

export function FixConflictSheet({
  visible,
  onClose,
  onSwap,
  kicker = 'INSTEAD OF BIOTECH PANEL',
  headline = '3 things you can make.',
  verb = 'Swap in',
}: {
  visible: boolean;
  onClose: () => void;
  onSwap: (alternativeId: string) => void;
  kicker?: string;
  headline?: string;
  verb?: string;
}) {
  const [selectedId, setSelectedId] = useState(alternatives[0].id);
  const selected = alternatives.find((item) => item.id === selectedId) ?? alternatives[0];

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <Pressable style={styles.dismiss} onPress={onClose} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.heading}>
            <View style={styles.headingCopy}>
              <Text style={styles.kicker}>{kicker}</Text>
              <Text style={styles.title}>{headline}</Text>
              <Text style={styles.sub}>Same gap. A little more breathing room.</Text>
            </View>
            <Pressable onPress={onClose} style={styles.close}>
              <Text style={styles.closeMark}>×</Text>
            </Pressable>
          </View>

          {alternatives.map((option) => (
            <OptionCard
              key={option.id}
              option={option}
              selected={option.id === selectedId}
              onPress={() => setSelectedId(option.id)}
            />
          ))}

          <Pressable onPress={() => onSwap(selected.id)} style={styles.swap}>
            <Text style={styles.swapText}>{verb} {selected.addLabel}</Text>
          </Pressable>
          <Text style={styles.note}>Includes the walk to your 2:00 PM lab.</Text>
        </View>
      </View>
    </Modal>
  );
}

function OptionCard({
  option,
  selected,
  onPress,
}: {
  option: Alternative;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={[styles.option, selected && styles.optionOn, option.fit === 'tight' && styles.optionTight]}>
      <View style={[styles.radio, selected && styles.radioOn]} />
      <View style={styles.optionCopy}>
        <Text style={styles.optionTitle}>{option.title}</Text>
        <Text style={styles.optionMeta}>{option.meta}</Text>
      </View>
      <View style={[styles.pill, option.fit === 'tight' && styles.pillTight]}>
        <Text style={[styles.pillText, option.fit === 'tight' && styles.pillTightText]}>{option.spare}</Text>
      </View>
    </Pressable>
  );
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
  heading: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, marginBottom: 12 },
  headingCopy: { flex: 1 },
  kicker: { letterSpacing: 0.8, fontSize: 11, color: colors.muted },
  title: { marginTop: 4, fontSize: 26, color: colors.ink, fontFamily: 'Georgia' },
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
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderWidth: 1.5,
    borderColor: colors.line,
    borderRadius: 16,
    backgroundColor: colors.white,
    padding: 12,
    marginBottom: 8,
  },
  optionOn: { borderColor: colors.ink },
  optionTight: { borderStyle: 'dashed' },
  radio: { width: 16, height: 16, borderRadius: 8, borderWidth: 1.5, borderColor: colors.ink },
  radioOn: { backgroundColor: colors.orange, borderColor: colors.orange },
  optionCopy: { flex: 1 },
  optionTitle: { fontSize: 16, color: colors.ink },
  optionMeta: { marginTop: 2, color: colors.muted, fontSize: 13 },
  pill: { backgroundColor: colors.greenBg, borderRadius: 12, paddingHorizontal: 8, paddingVertical: 4 },
  pillTight: { backgroundColor: colors.yellowBg },
  pillText: { color: colors.green, fontSize: 12 },
  pillTightText: { color: colors.yellowInk },
  swap: {
    marginTop: 8,
    backgroundColor: colors.orange,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.ink,
    paddingVertical: 14,
    alignItems: 'center',
  },
  swapText: { color: colors.white, fontSize: 16 },
  note: { marginTop: 8, textAlign: 'center', color: colors.muted, fontSize: 13 },
});
