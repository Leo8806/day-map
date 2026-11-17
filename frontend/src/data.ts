export type Fit = 'fits' | 'tight' | 'wont';

export type Category =
  | 'Academic'
  | 'Career'
  | 'Research'
  | 'Art'
  | 'Sports'
  | 'Tech'
  | 'Social'
  | 'Food';

export type Building = {
  id: string;
  name: string;
  walk: string;
};

export type CampusEvent = {
  id: string;
  title: string;
  buildingId: string;
  category: Category;
  eyebrow: string;
  place: string;
  when: string;
  startHour: number;
  fit: Fit;
  spare: string;
  destination: string;
};

export type DayBlock = {
  id: string;
  time: string;
  title: string;
  place: string;
  fromCalendar?: boolean;
  conflict?: boolean;
  conflictNote?: string;
};

export type Alternative = {
  id: string;
  title: string;
  meta: string;
  fit: Fit;
  spare: string;
  addLabel: string;
};

export const categories: Category[] = [
  'Academic',
  'Career',
  'Research',
  'Art',
  'Sports',
  'Tech',
  'Social',
  'Food',
];

export const mapChips: Category[] = ['Career', 'Research', 'Social'];

export const buildings: Building[] = [
  { id: 'huntsman', name: 'Huntsman', walk: '6 min walk from Towne.' },
  { id: 'houston', name: 'Houston Hall', walk: '6 min walk from Towne.' },
  { id: 'towne', name: 'Towne', walk: "You're here · Towne 100." },
  { id: 'vanpelt', name: 'Van Pelt', walk: '6 min walk from Towne.' },
  { id: 'levine', name: 'Levine', walk: '6 min walk from Towne.' },
];

export const events: CampusEvent[] = [
  {
    id: 'coffee-chat',
    title: 'Biotech coffee chat',
    buildingId: 'houston',
    category: 'Career',
    eyebrow: 'CAREER · BIOTECHNOLOGY',
    place: 'Houston Hall · 2nd floor',
    when: 'Today, Tuesday · 12:30–1:15 PM',
    startHour: 12.5,
    fit: 'fits',
    spare: 'fits · 9 min spare',
    destination: 'Houston',
  },
  {
    id: 'grad-info',
    title: 'Grad info session',
    buildingId: 'houston',
    category: 'Academic',
    eyebrow: 'ACADEMIC · BIOTECHNOLOGY',
    place: 'Houston Hall · 2nd floor',
    when: 'Today, Tuesday · 1:05–1:50 PM',
    startHour: 13.1,
    fit: 'tight',
    spare: 'tight · 1 min',
    destination: 'Houston',
  },
  {
    id: 'econ-house',
    title: 'Econ open house',
    buildingId: 'houston',
    category: 'Social',
    eyebrow: 'SOCIAL · ECONOMICS',
    place: 'Houston Hall · 1st floor',
    when: 'Today, Tuesday · 1:40–2:30 PM',
    startHour: 13.7,
    fit: 'wont',
    spare: "won't make it",
    destination: 'Houston',
  },
  {
    id: 'research-dropin',
    title: 'Research drop-in',
    buildingId: 'huntsman',
    category: 'Research',
    eyebrow: 'RESEARCH · BIOTECHNOLOGY',
    place: 'Huntsman · 2nd floor',
    when: 'Today, Tuesday · 12:30–1:00 PM',
    startHour: 12.5,
    fit: 'fits',
    spare: 'fits · 12 min spare',
    destination: 'Huntsman',
  },
  {
    id: 'lab-tour',
    title: 'Bioeng lab tour',
    buildingId: 'towne',
    category: 'Research',
    eyebrow: 'RESEARCH · BIOTECHNOLOGY',
    place: 'Towne · 2nd floor',
    when: 'Today, Tuesday · 1:20–1:50 PM',
    startHour: 13.3,
    fit: 'fits',
    spare: 'fits · 4 min spare',
    destination: 'Towne',
  },
  {
    id: 'reading-group',
    title: 'Student reading group',
    buildingId: 'vanpelt',
    category: 'Academic',
    eyebrow: 'ACADEMIC · CAMPUS',
    place: 'Van Pelt · 1st floor',
    when: 'Today, Tuesday · 1:30–2:30 PM',
    startHour: 13.5,
    fit: 'wont',
    spare: "won't make it",
    destination: 'Van Pelt',
  },
  {
    id: 'biotech-panel',
    title: 'Biotech panel',
    buildingId: 'levine',
    category: 'Research',
    eyebrow: 'RESEARCH · BIOTECHNOLOGY',
    place: 'Levine',
    when: 'Today, Tuesday · 1:20–2:00 PM',
    startHour: 13.3,
    fit: 'wont',
    spare: "won't make it",
    destination: 'Levine',
  },
];

export const alternatives: Alternative[] = [
  {
    id: 'lab-tour',
    title: 'Bioeng lab tour',
    meta: '1:20–1:50 · Towne',
    fit: 'fits',
    spare: 'fits · 4 min',
    addLabel: 'Bioengineering lab tour',
  },
  {
    id: 'pharma',
    title: 'Pharma panel',
    meta: '1:15–1:55 · Huntsman',
    fit: 'fits',
    spare: 'fits · 7 min',
    addLabel: 'Pharma panel',
  },
  {
    id: 'startup',
    title: 'Startup office hrs',
    meta: '1:25–1:55 · Houston Hall',
    fit: 'tight',
    spare: 'tight · 2 min',
    addLabel: 'Startup office hrs',
  },
];

export const seededDay: DayBlock[] = [
  {
    id: 'intro',
    time: '10:30–11:45 AM',
    title: 'Intro to bioengineering',
    place: 'Towne · Room 100',
    fromCalendar: true,
  },
  {
    id: 'lunch',
    time: '12:00–12:15 PM',
    title: 'Lunch with Maya',
    place: 'Houston Hall',
  },
  {
    id: 'panel',
    time: '1:20–2:00 PM',
    title: 'Biotech panel',
    place: 'Levine',
    conflict: true,
    conflictNote: "won't make it — 6 min short",
  },
  {
    id: 'lab',
    time: '2:00–3:30 PM',
    title: 'Bioengineering lab',
    place: 'Levine · Room 204',
    fromCalendar: true,
  },
];

export const sharedDetail = {
  classNote: 'Class at Towne ends 11:45 · 4 min to get out · 6 min walk',
  arrive: 'Arrive 12:24, 6 min early',
  beforeLab: 'You can still reach Levine by 1:29 for your 2:00 lab.',
  going: '12 going · 3 people you follow',
  about:
    'Meet students and researchers in biotech. Coffee and informal conversation. All welcome.',
};

export const recentSearches = ['Houston Hall', 'Biotech', 'Research'];
