export function toMonthKey(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  return `${year}-${month}`;
}

export function toDateKey(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatDisplayDate(dateKey: string) {
  const date = new Date(`${dateKey}T00:00:00`);
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  }).format(date);
}

export function buildMonthGrid(monthKey: string) {
  const [yearValue, monthValue] = monthKey.split('-').map(Number);
  const firstDay = new Date(yearValue, monthValue - 1, 1);
  const lastDay = new Date(yearValue, monthValue, 0);
  const leadingEmptyCells = firstDay.getDay();
  const days = Array.from({ length: lastDay.getDate() }, (_, index) => {
    const value = index + 1;
    const date = new Date(yearValue, monthValue - 1, value);
    return {
      day: value,
      dateKey: toDateKey(date),
    };
  });

  return {
    year: yearValue,
    month: monthValue,
    leadingEmptyCells,
    days,
  };
}

export function formatMonthHeading(monthKey: string) {
  const [yearValue, monthValue] = monthKey.split('-').map(Number);
  return {
    yearLabel: `${yearValue}`,
    monthLabel: `${monthValue}月`,
  };
}
