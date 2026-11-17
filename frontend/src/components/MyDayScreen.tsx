import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { alternatives, seededDay, type DayBlock } from '../data';
import { colors } from '../theme';
import { FixConflictSheet } from './FixConflictSheet';

const walkAfter: Record<string, { label: string; good: boolean }> = {
  intro: { label: '6 min walk · fits', good: true },
  lunch: { label: '14 min walk · 6 min short', good: false },
  panel: { label: '4 min walk · no time to spare', good: false },
};

const resolvedWalks: Record<string, { label: string; good: boolean }> = {
  intro: { label: '6 min walk · fits', good: true },
  lunch: { label: '6 min walk · fits', good: true },
  panel: { label: '4 min walk · fits', good: true },
};

export function MyDayScreen() {
  const [fixing, setFixing] = useState(false);
  const [replacementId, setReplacementId] = useState<string | null>(null);
  const day = seededDay.map((block) => swappedBlock(block, replacementId));
  const walks = replacementId ? resolvedWalks : walkAfter;

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>My day</Text>
          <Text style={styles.wordmark}>DAY MAP</Text>
        </View>
        <View style={styles.subhead}>
          <Text style={styles.date}>Today · Tuesday</Text>
          <View style={styles.countPill}>
            <Text style={styles.countText}>{day.length} events</Text>
          </View>
        </View>

        {day.map((block) => (
          <View key={block.id}>
            <DayCard block={block} />
            {walks[block.id] ? (
              <Text style={[styles.walk, walks[block.id].good ? styles.walkGood : styles.walkBad]}>
                {walks[block.id].label}
              </Text>
            ) : null}
          </View>
        ))}
      </ScrollView>

      {replacementId ? (
        <View style={styles.resolved}>
          <Text style={styles.resolvedText}>✓  Everything in your day fits.</Text>
        </View>
      ) : (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>!  One conflict in your day</Text>
          <Pressable style={styles.fix} onPress={() => setFixing(true)}>
            <Text style={styles.fixText}>Fix it →</Text>
          </Pressable>
        </View>
      )}
      <FixConflictSheet
        visible={fixing}
        onClose={() => setFixing(false)}
        onSwap={(alternativeId) => {
          setReplacementId(alternativeId);
          setFixing(false);
        }}
      />
    </View>
  );
}

function swappedBlock(block: DayBlock, replacementId: string | null): DayBlock {
  if (block.id !== 'panel' || !replacementId) return block;
  const alternative = alternatives.find((item) => item.id === replacementId);
  if (!alternative) return block;
  const [time, place] = alternative.meta.split(' · ');
  return {
    ...block,
    title: alternative.title,
    time: `${time} PM`,
    place,
    conflict: false,
    conflictNote: undefined,
  };
}

function DayCard({ block }: { block: DayBlock }) {
  return (
    <View style={styles.row}>
      <View style={styles.rail}>
        <View style={[styles.dot, block.conflict && styles.dotConflict]} />
      </View>
      <View style={[styles.card, block.conflict && styles.cardConflict]}>
        <Text style={styles.time}>{block.time}</Text>
        <Text style={[styles.cardTitle, block.conflict && styles.cardTitleConflict]}>{block.title}</Text>
        <Text style={styles.place}>{block.place}</Text>
        {block.fromCalendar ? <Text style={styles.calendar}>▦  from Google Calendar</Text> : null}
        {block.conflictNote ? <Text style={styles.conflictNote}>{block.conflictNote}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { paddingHorizontal: 20, paddingBottom: 16 },
  header: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 },
  title: { fontSize: 40, color: colors.ink, fontFamily: 'Georgia' },
  wordmark: { fontSize: 11, letterSpacing: 1.2, color: colors.muted, marginBottom: 10 },
  subhead: { marginTop: 16, marginBottom: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  date: { color: colors.ink, fontSize: 15 },
  countPill: { borderWidth: 1, borderColor: colors.line, borderRadius: 14, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: colors.white },
  countText: { color: colors.muted, fontSize: 13 },
  row: { flexDirection: 'row', gap: 10 },
  rail: { width: 16, alignItems: 'center', paddingTop: 16 },
  dot: { width: 10, height: 10, borderRadius: 5, borderWidth: 1.5, borderColor: colors.ink, backgroundColor: colors.bg },
  dotConflict: { backgroundColor: colors.orange, borderColor: colors.orange },
  card: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 14,
    backgroundColor: colors.white,
    padding: 12,
    marginBottom: 4,
  },
  cardConflict: { backgroundColor: colors.cardMuted, borderColor: colors.line },
  time: { color: colors.muted, fontSize: 13 },
  cardTitle: { marginTop: 2, fontSize: 18, color: colors.ink, fontFamily: 'Georgia' },
  cardTitleConflict: { color: colors.muted },
  place: { marginTop: 2, color: colors.muted },
  calendar: { marginTop: 8, color: colors.muted, fontSize: 13 },
  conflictNote: { marginTop: 8, color: colors.danger, fontSize: 14 },
  walk: { marginLeft: 26, marginBottom: 8, fontSize: 14, fontStyle: 'italic' },
  walkGood: { color: colors.green },
  walkBad: { color: colors.danger },
  banner: {
    marginHorizontal: 20,
    marginBottom: 8,
    backgroundColor: colors.dangerBg,
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  bannerText: { color: colors.ink, flex: 1 },
  fix: { backgroundColor: colors.black, borderRadius: 16, paddingHorizontal: 14, paddingVertical: 8 },
  fixText: { color: colors.white },
  resolved: {
    alignSelf: 'center',
    marginBottom: 10,
    backgroundColor: colors.greenBg,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  resolvedText: { color: colors.green },
});
