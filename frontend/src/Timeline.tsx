import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";

import { timeline } from "./demo";

export function Timeline() {
  return (
    <section className="timeline panel" aria-label="Investigation timeline">
      <div className="timeline-toolbar">
        <div>
          <h2>Investigation timeline</h2>
          <div className="timeline-tabs">
            <button className="active" type="button">All events</button>
            <button type="button">Transactions</button>
            <button type="button">Documents</button>
            <button type="button">AI analysis</button>
            <button type="button">Human review</button>
          </div>
        </div>
        <div className="date-range">
          <button aria-label="Previous period" type="button"><ChevronLeft size={14} /></button>
          <span><CalendarDays size={14} /> May 12 — May 19, 2026</span>
          <button aria-label="Next period" type="button"><ChevronRight size={14} /></button>
        </div>
      </div>
      <div className="timeline-events">
        {timeline.map((event) => (
          <article className={`timeline-event ${event.kind}`} key={event.id}>
            <span className="event-date">{event.date}</span>
            <i />
            <div>
              <time>{event.time}</time>
              <strong>{event.title}</strong>
              <p>{event.detail}</p>
            </div>
          </article>
        ))}
      </div>
      <div className="activity-strip" aria-label="Event activity overview">
        {Array.from({ length: 72 }, (_, index) => (
          <i key={index} style={{ height: `${8 + ((index * 17) % 32)}%` }} />
        ))}
      </div>
    </section>
  );
}
