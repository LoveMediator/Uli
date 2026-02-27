import { useState, useEffect } from 'react';
import { useCalendar } from '../hooks';

export const CalendarExample = () => {
  const {
    calendarData,
    reviews,
    isLoading,
    error,
    fetchCalendar,
    fetchReviewsByDate,
  } = useCalendar();

  const [selectedDate, setSelectedDate] = useState('');
  const currentDate = new Date();
  const [year, setYear] = useState(currentDate.getFullYear());
  const [month, setMonth] = useState(currentDate.getMonth() + 1);

  useEffect(() => {
    fetchCalendar(year, month);
  }, [year, month, fetchCalendar]);

  const handleDateClick = async (date: string) => {
    setSelectedDate(date);
    await fetchReviewsByDate(date);
  };

  const handlePrevMonth = () => {
    if (month === 1) {
      setYear(year - 1);
      setMonth(12);
    } else {
      setMonth(month - 1);
    }
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setYear(year + 1);
      setMonth(1);
    } else {
      setMonth(month + 1);
    }
  };

  return (
    <div>
      <h2>吵架日历</h2>

      {/* 月份导航 */}
      <div>
        <button onClick={handlePrevMonth}>上个月</button>
        <span>{year}年{month}月</span>
        <button onClick={handleNextMonth}>下个月</button>
      </div>

      {/* 日历视图 */}
      {isLoading && <p>加载中...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {calendarData && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px' }}>
            {['日', '一', '二', '三', '四', '五', '六'].map((day) => (
              <div key={day} style={{ fontWeight: 'bold', textAlign: 'center' }}>
                {day}
              </div>
            ))}
            {calendarData.days.map((day) => (
              <div
                key={day.date}
                onClick={() => day.hasReviews && handleDateClick(day.date)}
                style={{
                  padding: '8px',
                  textAlign: 'center',
                  cursor: day.hasReviews ? 'pointer' : 'default',
                  backgroundColor: day.hasReviews ? '#ffebee' : 'transparent',
                  border: selectedDate === day.date ? '2px solid red' : '1px solid #ddd',
                }}
              >
                {new Date(day.date).getDate()}
                {day.hasReviews && <div style={{ fontSize: '12px' }}>({day.reviewCount})</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 复盘列表 */}
      {selectedDate && (
        <div style={{ marginTop: '20px' }}>
          <h3>{selectedDate} 的复盘记录</h3>
          {reviews.length === 0 ? (
            <p>该日期无复盘记录</p>
          ) : (
            <ul>
              {reviews.map((review) => (
                <li key={review.id}>
                  <strong>{review.title}</strong>
                  <p>{review.summary}</p>
                  <p>
                    责任比例 - A: {review.aResponsibility}% | B: {review.bResponsibility}%
                  </p>
                  <p>标签: {review.tags.join(', ')}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
