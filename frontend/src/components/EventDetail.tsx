import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { events, sharedDetail } from '../data';
import { colors } from '../theme';
import { FixConflictSheet } from './FixConflictSheet';

export function EventDetail({
  eventId,
  onBack,
  onViewDay,
}: {
  eventId: string;
  onBack: () => void;
  onViewDay: () => void;
}) {
  const event = events.find((item) => item.id === eventId);
  const [added, setAdded] = useState(false);
  const [finding, setFinding] = useState(false);
  if (!event) return null;

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Pressable onPress={onBack} style={styles.back}>
            <Text style={styles.backMark}>←</Text>
            <Text style={styles.backLabel}>Event details</Text>
          </Pressable>
          <Text style={styles.wordmark}>DAY MAP</Text>
        </View>

        <Text style={styles.eyebrow}>{event.eyebrow}</Text>
        <Text style={styles.title}>{event.title}</Text>
        <Text style={styles.meta}>⌂  {event.place}</Text>
        <Text style={styles.meta}>◷  {event.when}</Text>

        <View style={styles.fitCard}>
          <Text style={styles.kicker}>DOES IT FIT?</Text>
          <Text style={styles.body}>{sharedDetail.classNote}</Text>
          <Text style={styles.arrive}>{sharedDetail.arrive}</Text>
          <View style={[styles.spare, event.fit === 'tight' && styles.spareTight, event.fit === 'wont' && styles.spareWont]}>
            <Text
              style={[
                styles.spareText,
                event.fit === 'tight' && styles.spareTightText,
                event.fit === 'wont' && styles.spareWontText,
              ]}
            >
              {event.spare}
            </Text>
          </View>
          <View style={styles.walk}>
            <View style={styles.stop}>
              <Text style={styles.stopText}>Towne</Text>
            </View>
            <Text style={styles.walkTime}>6 min</Text>
            <View style={[styles.stop, styles.stopEnd]}>
              <Text style={styles.stopText}>{event.destination}</Text>
            </View>
          </View>
        </View>

        <View style={styles.before}>
          <Text style={styles.beforeKicker}>BEFORE YOUR LAB</Text>
          <Text style={styles.beforeBody}>{sharedDetail.beforeLab}</Text>
        </View>

        <Text style={styles.section}>WHO'S GOING</Text>
        <View style={styles.going}>
          {['MA', 'JL', 'RK'].map((initials, index) => (
            <View key={initials} style={[styles.avatar, { marginLeft: index === 0 ? 0 : -8 }]}>
              <Text style={styles.avatarText}>{initials}</Text>
            </View>
          ))}
          <Text style={styles.goingText}>{sharedDetail.going}</Text>
        </View>

        <Text style={styles.section}>ABOUT THIS EVENT</Text>
        <Text style={styles.about}>{sharedDetail.about}</Text>
      </ScrollView>

      <View style={styles.footer}>
        {added ? null : (
          <Pressable onPress={() => setFinding(true)}>
            <Text style={styles.find}>Find another way</Text>
          </Pressable>
        )}
        {added ? (
          <View style={styles.added}>
            <Text style={styles.addedText}>✓  Added to your day</Text>
            <Pressable onPress={onViewDay}>
              <Text style={styles.viewDay}>View day →</Text>
            </Pressable>
          </View>
        ) : (
          <Pressable onPress={() => setAdded(true)} style={styles.add}>
            <Text style={styles.addText}>Add to my day</Text>
          </Pressable>
        )}
      </View>
      <FixConflictSheet
        visible={finding}
        kicker="FIND ANOTHER WAY"
        headline="Instead of this event"
        verb="Add"
        onClose={() => setFinding(false)}
        onSwap={() => {
          setFinding(false);
          setAdded(true);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { paddingHorizontal: 20, paddingBottom: 16 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 },
  back: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  backMark: { fontSize: 18, color: colors.ink },
  backLabel: { fontSize: 16, color: colors.ink },
  wordmark: { fontSize: 11, letterSpacing: 1.2, color: colors.muted },
  eyebrow: { marginTop: 22, color: colors.orange, letterSpacing: 0.6, fontSize: 12 },
  title: { marginTop: 6, fontSize: 32, color: colors.ink, fontFamily: 'Georgia' },
  meta: { marginTop: 6, color: colors.muted, fontSize: 14 },
  fitCard: {
    marginTop: 18,
    borderWidth: 1.5,
    borderColor: colors.ink,
    borderRadius: 16,
    backgroundColor: colors.white,
    padding: 14,
  },
  kicker: { fontSize: 11, letterSpacing: 0.8, color: colors.muted },
  body: { marginTop: 6, color: colors.ink, lineHeight: 20 },
  arrive: {
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: colors.yellowBg,
    color: colors.ink,
    fontSize: 18,
    fontFamily: 'Georgia',
  },
  spare: {
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: colors.greenBg,
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  spareTight: { backgroundColor: colors.yellowBg },
  spareWont: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.line },
  spareText: { color: colors.green, fontSize: 13 },
  spareTightText: { color: colors.yellowInk },
  spareWontText: { color: colors.muted },
  walk: { marginTop: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  stop: { borderWidth: 1.5, borderColor: colors.ink, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: colors.white },
  stopEnd: { backgroundColor: colors.greenSoft },
  stopText: { color: colors.ink },
  walkTime: { color: colors.orange, fontSize: 13 },
  before: { marginTop: 12, backgroundColor: colors.greenCard, borderRadius: 14, padding: 14 },
  beforeKicker: { color: colors.green, letterSpacing: 0.6, fontSize: 12 },
  beforeBody: { marginTop: 4, color: colors.ink, lineHeight: 20 },
  section: { marginTop: 18, letterSpacing: 0.6, fontSize: 12, color: colors.muted },
  going: { marginTop: 8, flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: colors.ink,
    backgroundColor: colors.yellowBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 11, color: colors.ink },
  goingText: { marginLeft: 8, color: colors.ink, flex: 1 },
  about: { marginTop: 8, fontSize: 16, lineHeight: 22, color: colors.ink },
  footer: { paddingHorizontal: 20, paddingBottom: 8, gap: 10 },
  find: { textAlign: 'center', color: colors.ink, textDecorationLine: 'underline', fontSize: 15 },
  add: {
    backgroundColor: colors.orange,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.ink,
    paddingVertical: 14,
    alignItems: 'center',
  },
  addText: { color: colors.white, fontSize: 16 },
  added: {
    backgroundColor: colors.black,
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  addedText: { color: colors.white, fontSize: 15 },
  viewDay: { color: colors.yellow, fontSize: 15 },
});
