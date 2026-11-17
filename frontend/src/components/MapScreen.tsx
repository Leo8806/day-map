import { useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { buildings, events, mapChips, type Category } from '../data';
import { colors } from '../theme';
import { BuildingSheet } from './BuildingSheet';
import { EventDetail } from './EventDetail';
import { MyDayScreen } from './MyDayScreen';
import { SearchScreen } from './SearchScreen';

type Tone = 'green' | 'focus' | 'muted' | 'plain';

function categoryMatch(category: Category | null, eventCategory: Category) {
  return category == null || category === eventCategory;
}

function buildingTone(buildingId: string, category: Category | null, reachableOnly: boolean): Tone {
  const atBuilding = events.filter(
    (event) => event.buildingId === buildingId && categoryMatch(category, event.category),
  );
  const shown = reachableOnly ? atBuilding.filter((event) => event.fit !== 'wont') : atBuilding;
  if (shown.length === 0) return 'muted';
  if (buildingId === 'houston') return 'focus';
  if (shown.some((event) => event.fit === 'fits')) return 'green';
  return 'plain';
}

export function MapScreen() {
  const [reachableOnly, setReachableOnly] = useState(true);
  const [category, setCategory] = useState<Category | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [eventId, setEventId] = useState<string | null>(null);
  const [tab, setTab] = useState<'map' | 'day'>('map');
  const [searching, setSearching] = useState(false);

  const selectedBuilding = buildings.find((building) => building.id === selectedId) ?? null;

  const reachableCount = events.filter((event) => {
    if (!categoryMatch(category, event.category)) return false;
    return reachableOnly ? event.fit !== 'wont' : true;
  }).length;

  return (
    <SafeAreaView style={styles.screen}>
      {tab === 'day' ? (
        <MyDayScreen />
      ) : searching ? (
        <SearchScreen
          onCancel={() => setSearching(false)}
          onOpenEvent={(id) => {
            setSearching(false);
            setEventId(id);
          }}
        />
      ) : eventId ? (
        <EventDetail
          eventId={eventId}
          onBack={() => setEventId(null)}
          onViewDay={() => {
            setEventId(null);
            setTab('day');
          }}
        />
      ) : (
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Map</Text>
            <Pressable onPress={() => setSearching(true)} style={styles.search}>
              <Text style={styles.searchMark}>⌕</Text>
            </Pressable>
          </View>
          <Text style={styles.wordmark}>DAY MAP</Text>
        </View>

        <View style={styles.freeCard}>
          <View style={styles.freeCopy}>
            <Text style={styles.freeLabel}>FREE UNTIL</Text>
            <Text style={styles.freeTitle}>2:00 PM lab</Text>
          </View>
          <View style={styles.freeRule} />
          <View style={styles.freeCopy}>
            <Text style={styles.minutes}>58 min</Text>
            <Text style={styles.freeHint}>to explore</Text>
          </View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
          <Pressable
            onPress={() => setReachableOnly((on) => !on)}
            style={[styles.chip, reachableOnly && styles.chipOn]}
          >
            <Text style={[styles.chipText, reachableOnly && styles.chipTextOn]}>
              {reachableOnly ? '✓  ' : ''}Reachable only
            </Text>
          </Pressable>
          {mapChips.map((chip) => {
            const on = category === chip;
            return (
              <Pressable
                key={chip}
                onPress={() => setCategory(on ? null : chip)}
                style={[styles.chip, on && styles.chipOn]}
              >
                <Text style={[styles.chipText, on && styles.chipTextOn]}>{chip}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={styles.meta}>
          <Text style={styles.metaText}>University City</Text>
          <Text style={styles.metaText}>Today · 12:02 PM</Text>
        </View>

        <View style={styles.map}>
          <Text style={styles.street}>WALNUT ST</Text>
          <View style={styles.row}>
            <BuildingBlock id="huntsman" category={category} reachableOnly={reachableOnly} selected={selectedId === 'huntsman'} onPress={setSelectedId} />
            <BuildingBlock id="houston" category={category} reachableOnly={reachableOnly} selected={selectedId === 'houston'} onPress={setSelectedId} wide />
            <BuildingBlock id="vanpelt" category={category} reachableOnly={reachableOnly} selected={selectedId === 'vanpelt'} onPress={setSelectedId} />
          </View>
          <Text style={styles.streetRight}>LOCUST WALK</Text>
          <View style={styles.row}>
            <View style={styles.trees}>
              <View style={styles.tree} />
              <View style={[styles.tree, styles.treeSmall]} />
              <View style={styles.tree} />
            </View>
            <BuildingBlock id="towne" category={category} reachableOnly={reachableOnly} selected={selectedId === 'towne'} onPress={setSelectedId} wide />
            <BuildingBlock id="levine" category={category} reachableOnly={reachableOnly} selected={selectedId === 'levine'} onPress={setSelectedId} />
          </View>
          <View style={styles.here}>
            <View style={styles.hereDot} />
            <Text style={styles.hereText}>you are here</Text>
          </View>
          <Text style={styles.walkNote}>6 min</Text>
        </View>

        <View style={styles.legend}>
          <Legend swatch={colors.green} label="fits" />
          <Legend swatch={colors.yellow} label="tight" dashed />
          <Legend swatch={colors.faint} label="won't make it" hollow />
        </View>

        <View style={styles.summary}>
          <View style={styles.summaryDot} />
          <Text style={styles.summaryText}>
            {reachableCount} of {events.length} reachable before your lab
          </Text>
        </View>
        <Text style={styles.hint}>Tap a building to see what fits.</Text>
      </ScrollView>
      )}

      <View style={styles.tabs}>
        <Pressable style={styles.tab} onPress={() => setTab('map')}>
          <Text style={[styles.tabIcon, tab !== 'map' && styles.tabIdleIcon]}>▣</Text>
          <Text style={[styles.tabLabel, tab !== 'map' && styles.tabIdle]}>Map</Text>
          {tab === 'map' ? <View style={styles.tabMark} /> : null}
        </Pressable>
        <Pressable
          style={styles.tab}
          onPress={() => {
            setEventId(null);
            setSelectedId(null);
            setSearching(false);
            setTab('day');
          }}
        >
          <Text style={[styles.tabIcon, tab !== 'day' && styles.tabIdleIcon]}>▦</Text>
          <Text style={[styles.tabLabel, tab !== 'day' && styles.tabIdle]}>My day</Text>
          {tab === 'day' ? <View style={styles.tabMark} /> : null}
        </Pressable>
      </View>
      <BuildingSheet
        building={eventId || searching || tab === 'day' ? null : selectedBuilding}
        onClose={() => setSelectedId(null)}
        onOpenEvent={setEventId}
      />
    </SafeAreaView>
  );
}

function BuildingBlock({
  id,
  category,
  reachableOnly,
  selected,
  onPress,
  wide,
}: {
  id: string;
  category: Category | null;
  reachableOnly: boolean;
  selected: boolean;
  onPress: (id: string) => void;
  wide?: boolean;
}) {
  const building = buildings.find((item) => item.id === id);
  const count = events.filter((event) => event.buildingId === id).length;
  const tone = buildingTone(id, category, reachableOnly);
  const palette = {
    green: { backgroundColor: colors.greenSoft, borderColor: colors.ink, color: colors.ink },
    focus: { backgroundColor: colors.white, borderColor: colors.ink, color: colors.ink },
    muted: { backgroundColor: colors.cardMuted, borderColor: colors.line, color: colors.faint },
    plain: { backgroundColor: colors.white, borderColor: colors.ink, color: colors.ink },
  }[tone];

  return (
    <Pressable
      onPress={() => onPress(id)}
      style={[
        styles.building,
        wide && styles.buildingWide,
        { backgroundColor: palette.backgroundColor, borderColor: palette.borderColor },
        tone === 'focus' && styles.buildingFocus,
        selected && styles.buildingSelected,
      ]}
    >
      <View style={[styles.badge, tone === 'muted' && styles.badgeMuted]}>
        <Text style={[styles.badgeText, tone === 'muted' && styles.badgeTextMuted]}>{count}</Text>
      </View>
      <Text style={[styles.buildingName, { color: palette.color }]}>{building?.name}</Text>
    </Pressable>
  );
}

function Legend({ swatch, label, dashed, hollow }: { swatch: string; label: string; dashed?: boolean; hollow?: boolean }) {
  return (
    <View style={styles.legendItem}>
      <View
        style={[
          styles.legendDot,
          { backgroundColor: hollow ? 'transparent' : swatch, borderColor: swatch },
          dashed && styles.legendDashed,
        ]}
      />
      <Text style={styles.legendLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { paddingHorizontal: 20, paddingBottom: 12 },
  header: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { fontSize: 40, color: colors.ink, fontFamily: 'Georgia' },
  search: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchMark: { fontSize: 18, color: colors.ink, marginTop: -2 },
  wordmark: { fontSize: 11, letterSpacing: 1.2, color: colors.muted, marginBottom: 10 },
  freeCard: {
    marginTop: 16,
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 18,
    backgroundColor: colors.white,
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  freeCopy: { flex: 1 },
  freeLabel: { fontSize: 11, letterSpacing: 0.8, color: colors.muted },
  freeTitle: { marginTop: 2, fontSize: 22, color: colors.ink, fontFamily: 'Georgia' },
  freeRule: { width: 1, alignSelf: 'stretch', backgroundColor: colors.line, marginHorizontal: 12 },
  minutes: { fontSize: 28, color: colors.ink, fontFamily: 'Georgia', backgroundColor: colors.yellowBg },
  freeHint: { color: colors.muted, marginTop: 2 },
  chips: { gap: 8, paddingVertical: 14 },
  chip: {
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    backgroundColor: colors.white,
  },
  chipOn: { backgroundColor: colors.black, borderColor: colors.black },
  chipText: { color: colors.ink, fontSize: 14 },
  chipTextOn: { color: colors.white },
  meta: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  metaText: { color: colors.muted, fontSize: 13 },
  map: {
    backgroundColor: colors.map,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 10,
    minHeight: 280,
  },
  street: { fontSize: 10, letterSpacing: 0.8, color: colors.muted, marginBottom: 6 },
  streetRight: { alignSelf: 'flex-end', fontSize: 10, letterSpacing: 0.8, color: colors.muted, marginVertical: 6 },
  row: { flexDirection: 'row', gap: 8, alignItems: 'stretch' },
  trees: { width: 54, justifyContent: 'center', gap: 6, paddingLeft: 6 },
  tree: { width: 16, height: 16, borderRadius: 8, backgroundColor: '#B7CDB4' },
  treeSmall: { width: 12, height: 12, marginLeft: 10 },
  building: {
    flex: 1,
    minHeight: 92,
    borderWidth: 1.5,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
  },
  buildingWide: { flex: 1.3 },
  buildingFocus: { borderWidth: 2.5 },
  buildingSelected: { transform: [{ scale: 0.98 }] },
  badge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
    backgroundColor: colors.white,
  },
  badgeMuted: { borderColor: colors.faint, backgroundColor: 'transparent' },
  badgeText: { fontSize: 12, color: colors.ink },
  badgeTextMuted: { color: colors.faint },
  buildingName: { textAlign: 'center', fontSize: 13 },
  here: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8, marginLeft: 88 },
  hereDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.orange },
  hereText: { color: colors.orange, fontSize: 13 },
  walkNote: { position: 'absolute', top: 108, left: 128, color: colors.orange, fontSize: 12 },
  legend: { flexDirection: 'row', gap: 14, marginTop: 14 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 10, height: 10, borderRadius: 5, borderWidth: 1.5 },
  legendDashed: { borderStyle: 'dashed' },
  legendLabel: { color: colors.ink, fontSize: 13 },
  summary: {
    marginTop: 14,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  summaryDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.green },
  summaryText: { color: colors.ink, fontSize: 13 },
  hint: { textAlign: 'center', color: colors.muted, marginTop: 8, fontSize: 13 },
  tabs: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.bg,
    paddingTop: 8,
    paddingBottom: 10,
  },
  tab: { flex: 1, alignItems: 'center', gap: 2 },
  tabIcon: { fontSize: 16, color: colors.ink },
  tabIdleIcon: { color: colors.faint },
  tabLabel: { fontSize: 12, color: colors.ink },
  tabIdle: { color: colors.muted },
  tabMark: { marginTop: 4, width: 28, height: 3, borderRadius: 2, backgroundColor: colors.orange },
});
