import { CalendarDays, ChevronLeft, ChevronRight, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

import { timeline } from "./demo";
import type { TimelineEvent } from "./types";

type TimelineFilter = "all" | TimelineEvent["kind"];

const tabs: { label: string; value: TimelineFilter }[] = [
  { label: "All events", value: "all" },
  { label: "Transactions", value: "transaction" },
  { label: "Documents", value: "document" },
  { label: "AI analysis", value: "ai" },
  { label: "Human review", value: "review" },
];

export function Timeline() {
  const [filter, setFilter] = useState<TimelineFilter>("all");
  const visibleEvents =
    filter === "all" ? timeline : timeline.filter((event) => event.kind === filter);

  return (
    <section className="timeline panel" aria-label="Investigation timeline">
      <div className="timeline-toolbar">
        <div>
          <div className="timeline-title">
            <h2>Investigation timeline</h2>
            <span>{visibleEvents.length} events</span>
          </div>
          <div className="timeline-tabs" aria-label="Timeline filters">
            {tabs.map((tab) => (
              <button
                aria-pressed={filter === tab.value}
                className={filter === tab.value ? "active" : ""}
                key={tab.value}
                onClick={() => setFilter(tab.value)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <div className="timeline-controls">
          <button className="filter-icon" aria-label="Timeline filter settings" type="button">
            <SlidersHorizontal size={14} />
          </button>
          <div className="date-range">
            <button aria-label="Previous period" type="button"><ChevronLeft size={14} /></button>
            <span><CalendarDays size={14} /> May 12 — May 19, 2026</span>
            <button aria-label="Next period" type="button"><ChevronRight size={14} /></button>
          </div>
        </div>
      </div>
      <div className="timeline-track">
        <div className="timeline-events">
          {visibleEvents.map((event) => (
            <article className={`timeline-event ${event.kind}`} key={event.id}>
              <span className="event-date">{event.date}</span>
              <i />
              <div>
                <time>{event.time} UTC</time>
                <strong>{event.title}</strong>
                <p>{event.detail}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
      <div className="activity-strip" aria-label="Event activity overview">
        {Array.from({ length: 72 }, (_, index) => (
          <i key={index} style={{ height: `${8 + ((index * 17) % 32)}%` }} />
        ))}
        <span style={{ left: "64%" }} />
      </div>
    </section>
  );
}
