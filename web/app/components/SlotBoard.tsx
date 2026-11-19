const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

// Weekday dates of November 2026, which starts on a Sunday.
const DATES = [
  2, 3, 4, 5, 6,
  9, 10, 11, 12, 13,
  16, 17, 18, 19, 20,
  23, 24, 25, 26, 27,
];

const OPEN_DATE = 19;
const OPEN_TIME = "9:40";

export function SlotBoard() {
  return (
    <figure
      className="board"
      role="img"
      aria-label={`A month of appointments at Brooklyn Atlantic Center. Every slot is taken except Thursday 19 November at ${OPEN_TIME} am.`}
    >
      <div className="boardHead">
        <span className="boardMonth">November 2026</span>
        <span className="boardOffice">Brooklyn Atlantic Center</span>
      </div>

      <div className="grid" aria-hidden="true">
        {WEEKDAYS.map((day) => (
          <span key={day} className="dayName">
            {day}
          </span>
        ))}

        {DATES.map((date) => {
          const isOpen = date === OPEN_DATE;
          return (
            <div key={date} className={isOpen ? "cell cellOpen" : "cell"}>
              <span className="cellDate">{date}</span>
              {isOpen && <span className="cellState">{OPEN_TIME}</span>}
            </div>
          );
        })}
      </div>

      <figcaption className="boardFoot">
        One slot freed up at 2:14 this morning. It was gone by 2:31.
      </figcaption>
    </figure>
  );
}
