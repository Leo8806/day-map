import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { buildings, events, recentSearches, type CampusEvent } from '../data';
import { colors } from '../theme';

export function SearchScreen({
  onCancel,
  onOpenEvent,
}: {
  onCancel: () => void;
  onOpenEvent: (eventId: string) => void;
}) {
  const [query, setQuery] = useState('');
  const needle = query.trim().toLowerCase();
  const results = needle
    ? events.filter((event) => {
        const building = buildings.find((item) => item.id === event.buildingId);
        const haystack = [event.title, event.category, event.place, building?.name ?? ''].join(' ').toLowerCase();
        return haystack.includes(needle);
      })
    : [];

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>Map</Text>
          <View style={styles.searchMark}>
            <Text style={styles.searchGlyph}>⌕</Text>
          </View>
        </View>
        <Text style={styles.wordmark}>DAY MAP</Text>
      </View>

      <View style={styles.fieldRow}>
        <View style={styles.field}>
          <Text style={styles.fieldGlyph}>⌕</Text>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search events, buildings..."
            placeholderTextColor={colors.faint}
            autoFocus
            style={styles.input}
          />
        </View>
        <Pressable onPress={onCancel}>
          <Text style={styles.cancel}>Cancel</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {needle ? (
          <>
            <Text style={styles.kicker}>RESULTS</Text>
            {results.length === 0 ? <Text style={styles.empty}>Nothing matches that search.</Text> : null}
            {results.map((event) => (
              <ResultCard key={event.id} event={event} onPress={() => onOpenEvent(event.id)} />
            ))}
          </>
        ) : (
          <>
            <Text style={styles.kicker}>RECENT SEARCHES</Text>
            {recentSearches.map((term) => (
              <Pressable key={term} onPress={() => setQuery(term)} style={styles.recent}>
                <View style={styles.clock}>
                  <Text style={styles.clockGlyph}>◷</Text>
                </View>
                <Text style={styles.recentText}>{term}</Text>
                <Text style={styles.chevron}>›</Text>
              </Pressable>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

function ResultCard({ event, onPress }: { event: CampusEvent; onPress: () => void }) {
  const building = buildings.find((item) => item.id === event.buildingId);
  const time = event.when.split(' · ').pop();
  const missed = event.fit === 'wont';

  return (
    <Pressable onPress={onPress} style={[styles.result, missed && styles.resultMissed]}>
      <Text style={[styles.resultTitle, missed && styles.resultTitleMissed]}>{event.title}</Text>
      <Text style={styles.resultMeta}>
        {building?.name} · {time}
      </Text>
      <View style={[styles.pill, missed && styles.pillMissed]}>
        <Text style={[styles.pillText, missed && styles.pillTextMissed]}>{event.spare}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', paddingHorizontal: 20, marginTop: 8 },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { fontSize: 40, color: colors.ink, fontFamily: 'Georgia' },
  searchMark: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchGlyph: { fontSize: 18, color: colors.ink, marginTop: -2 },
  wordmark: { fontSize: 11, letterSpacing: 1.2, color: colors.muted, marginBottom: 10 },
  fieldRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 20, marginTop: 16 },
  field: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 16,
    backgroundColor: colors.white,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  fieldGlyph: { color: colors.muted, fontSize: 16 },
  input: { flex: 1, fontSize: 16, color: colors.ink, padding: 0 },
  cancel: { color: colors.ink, fontSize: 16 },
  content: { paddingHorizontal: 20, paddingBottom: 24 },
  kicker: { marginTop: 22, marginBottom: 8, letterSpacing: 0.8, fontSize: 12, color: colors.muted },
  recent: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: colors.line },
  clock: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clockGlyph: { color: colors.muted, fontSize: 14 },
  recentText: { flex: 1, fontSize: 16, color: colors.ink },
  chevron: { color: colors.faint, fontSize: 22 },
  result: {
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 16,
    backgroundColor: colors.white,
    padding: 14,
    marginBottom: 10,
  },
  resultMissed: { backgroundColor: colors.cardMuted, borderColor: colors.line },
  resultTitle: { fontSize: 18, color: colors.ink, fontFamily: 'Georgia' },
  resultTitleMissed: { color: colors.muted },
  resultMeta: { marginTop: 4, color: colors.muted },
  pill: {
    marginTop: 8,
    alignSelf: 'flex-start',
    backgroundColor: colors.greenBg,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  pillMissed: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.line },
  pillText: { color: colors.green, fontSize: 12 },
  pillTextMissed: { color: colors.muted },
  empty: { color: colors.muted, marginTop: 8 },
});
