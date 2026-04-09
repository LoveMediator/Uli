import { buildMonthGrid, toDateKey, toMonthKey } from '@/shared/lib';

describe('date helpers', () => {
  it('builds month grid for a selected month', () => {
    const month = toMonthKey(new Date('2026-04-09T12:00:00+08:00'));
    const grid = buildMonthGrid(month);

    expect(month).toBe('2026-04');
    expect(grid.days.length).toBeGreaterThan(27);
    expect(grid.days[0]).toHaveProperty('dateKey');
  });

  it('creates yyyy-mm-dd date keys', () => {
    expect(toDateKey(new Date('2026-04-09T12:00:00+08:00'))).toBe('2026-04-09');
  });
});
