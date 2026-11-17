import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { events, type Building, type CampusEvent, type Fit } from '../data';
import { colors } from '../theme';

export function BuildingSheet({
  building,
  onClose,
  onOpenEvent,
}: {
  building: Building | null;
  onClose: () => void;
  onOpenEvent: (eventId: string) => void;
}) {
  const listed = events
    .filter((event) => event.buildingId === building?.id)
    .sort((a, b) => a.startHour - b.startHour);
  const countLabel = listed.length === 1 ? '1 event here' : `${listed.length} events here`;

  return (
    <Modal visible={building != null} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <Pressable style={styles.dismiss} onPress={onClose} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.heading}>
            <View style={styles.headingCopy}>
              <Text style={styles.kicker}>{building?.name.toUpperCase()}</Text>
              <Text style={styles.count}>{countLabel}</Text>
              <Text style={styles.walk}>{building?.walk}</Text>
            </View>
            <Pressable onPress={onClose} style={styles.close}>
              <Text style={styles.closeMark}>×</Text>
            </Pressable>
          </View>
          {listed.map((event) => (
            <EventRow key={event.id} event={event} onPress={() => onOpenEvent(event.id)} />
          ))}
          <Text style={styles.note}>Walking time includes getting back to your lab.</Text>
        </View>
      </View>
    </Modal>
  );
}

function EventRow({ event, onPress }: { event: CampusEvent; onPress: () => void }) {
  const time = event.when.split(' · ').pop();
  const reachable = event.fit !== 'wont';

  return (
    <Pressable onPress={onPress} style={styles.row}>
      <View style={styles.rowCopy}>
        <Text style={styles.time}>{time}</Text>
        <Text style={[styles.title, !reachable && styles.titleMuted]}>{event.title}</Text>
        <FitPill fit={event.fit} label={event.spare} />
      </View>
      <View style={[styles.plus, reachable ? styles.plusOn : styles.plusOff]}>
        <Text style={[styles.plusMark, reachable ? styles.plusMarkOn : styles.plusMarkOff]}>+</Text>
      </View>
    </Pressable>
  );
}

function FitPill({ fit, label }: { fit: Fit; label: string }) {
  const tone = {
    fits: { box: styles.pillFits, text: styles.pillFitsText },
    tight: { box: styles.pillTight, text: styles.pillTightText },
    wont: { box: styles.pillWont, text: styles.pillWontText },
  }[fit];

  return (
    <View style={[styles.pill, tone.box]}>
      <View style={[styles.dot, fit === 'fits' && styles.dotFits, fit === 'tight' && styles.dotTight, fit === 'wont' && styles.dotWont]} />
      <Text style={tone.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: colors.overlay },
  dismiss: { flex: 1 },
  sheet: {
    backgroundColor: colors.bg,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 22,
    paddingTop: 10,
    paddingBottom: 28,
  },
  handle: {
    alignSelf: 'center',
    width: 42,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.line,
    marginBottom: 16,
  },
  heading: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  headingCopy: { flex: 1 },
  kicker: { letterSpacing: 1, fontSize: 12, color: colors.muted },
  count: { marginTop: 4, fontSize: 28, color: colors.ink, fontFamily: 'Georgia' },
  walk: { marginTop: 4, color: colors.muted },
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
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    paddingVertical: 14,
  },
  rowCopy: { flex: 1, gap: 4 },
  time: { color: colors.muted, fontSize: 13 },
  title: { fontSize: 18, color: colors.ink, fontFamily: 'Georgia' },
  titleMuted: { color: colors.muted },
  plus: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  plusOn: { backgroundColor: colors.orange },
  plusOff: { backgroundColor: colors.cardMuted },
  plusMark: { fontSize: 24, marginTop: -2 },
  plusMarkOn: { color: colors.white },
  plusMarkOff: { color: colors.faint },
  note: { marginTop: 8, color: colors.muted, fontSize: 13 },
  pill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 14,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
  },
  pillFits: { backgroundColor: colors.greenBg, borderColor: colors.greenBg },
  pillFitsText: { color: colors.green, fontSize: 12 },
  pillTight: { backgroundColor: colors.yellowBg, borderColor: colors.yellow, borderStyle: 'dashed' },
  pillTightText: { color: colors.yellowInk, fontSize: 12 },
  pillWont: { backgroundColor: colors.white, borderColor: colors.line },
  pillWontText: { color: colors.muted, fontSize: 12 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  dotFits: { backgroundColor: colors.green },
  dotTight: { backgroundColor: colors.yellow },
  dotWont: { backgroundColor: colors.faint },
});
