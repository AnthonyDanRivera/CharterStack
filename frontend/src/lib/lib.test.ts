import { expect, test } from 'vitest'
import {
  addDays,
  fmtDuration,
  fmtEntered,
  fmtLong,
  fmtMoney,
  fmtUS,
  fmtWeekdayShort,
  shiftRange,
  todayIso,
} from './dates'
import { normalizeInitials } from './initials'
import { matchTimes, normalizeTime, TIME_LIST } from './time'

test('date formats', () => {
  expect(fmtLong('2026-11-09')).toBe('Mon, Nov 9, 2026')
  expect(fmtUS('2026-11-09')).toBe('11/09/2026')
  expect(fmtWeekdayShort('2026-11-09')).toBe('Mon 11/09')
  expect(fmtEntered('2026-11-04T10:12:00-05:00')).toBe('11/04 10:12')
  expect(fmtEntered(null)).toBe('')
  expect(fmtDuration(45 * 60 * 1000 + 12 * 60 * 60 * 1000 + 5000)).toBe('12:45:05')
})

test('day math crosses months and years', () => {
  expect(addDays('2026-12-31', 1)).toBe('2027-01-01')
  expect(addDays('2026-03-01', -1)).toBe('2026-02-28')
  expect(todayIso(new Date(2026, 10, 12, 23, 59))).toBe('2026-11-12')
})

test('previous/next shift the range by its own length (R24)', () => {
  expect(shiftRange('2026-11-09', '2026-11-09', 1)).toEqual({
    start: '2026-11-10',
    end: '2026-11-10',
  })
  expect(shiftRange('2026-11-09', '2026-11-11', 1)).toEqual({
    start: '2026-11-12',
    end: '2026-11-14',
  })
  expect(shiftRange('2026-11-09', '2026-11-11', -1)).toEqual({
    start: '2026-11-06',
    end: '2026-11-08',
  })
})

test('money display', () => {
  expect(fmtMoney('1200.00')).toBe('$1,200.00')
  expect(fmtMoney('0.00')).toBe('$0.00')
  expect(fmtMoney(null)).toBe('—')
})

test('time list and prefix matching', () => {
  expect(TIME_LIST).toHaveLength(96)
  expect(matchTimes('7').slice(0, 2)).toEqual(['07:00', '07:15'])
  expect(matchTimes('73')).toEqual(['07:30'])
  expect(matchTimes('7:30')).toEqual(['07:30'])
  expect(matchTimes('1915')).toEqual(['19:15'])
  expect(matchTimes('1916')).toEqual([])
  expect(matchTimes('19')[0]).toBe('19:00')
})

test('instant-feedback time normalization mirrors R02', () => {
  expect(normalizeTime('7')).toBe('07:00')
  expect(normalizeTime('730')).toBe('07:30')
  expect(normalizeTime('1915')).toBe('19:15')
  expect(normalizeTime('7 pm')).toBe('19:00')
  expect(normalizeTime('7:30PM')).toBe('19:30')
  expect(normalizeTime('25')).toBeNull()
  expect(normalizeTime('7:75')).toBeNull()
  expect(normalizeTime('ow')).toBeNull()
  expect(normalizeTime('ow', true)).toBe('One way')
})

test('initials normalization mirrors R22', () => {
  expect(normalizeInitials('a.r-1')).toBe('AR')
  expect(normalizeInitials('abcdef')).toBe('ABCD')
})
