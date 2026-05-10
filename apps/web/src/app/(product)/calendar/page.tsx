"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Clock, X } from "lucide-react";
import { ProductShell } from "@/components/product/ProductShell";
import { useProduct } from "@/hooks/useProduct";

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: "rgba(163,138,112,0.85)",
  twitter: "rgba(150,165,145,0.85)",
  instagram: "rgba(196,168,130,0.85)",
};

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  scheduled: { bg: "rgba(163,138,112,0.18)", text: "var(--bronze)" },
  published: { bg: "rgba(150,165,145,0.18)", text: "var(--olive)" },
  draft:     { bg: "var(--muted)",             text: "var(--text-muted)" },
};

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

export default function CalendarPage() {
  const product = useProduct();
  const calendar = product.calendar;
  const loadCalendar = product.loadCalendar;
  const [selectedEvent, setSelectedEvent] = useState<(typeof calendar)[0] | null>(null);

  const today = useMemo(() => new Date(), []);
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  useEffect(() => {
    void loadCalendar();
  }, [loadCalendar]);

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);
  const firstDay = getFirstDayOfWeek(viewYear, viewMonth);
  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;

  const monthLabel = new Date(viewYear, viewMonth).toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  const eventsByDay = useMemo(() => {
    const map: Record<number, typeof calendar> = {};
    for (const ev of calendar) {
      const d = new Date(ev.starts_at);
      if (d.getFullYear() === viewYear && d.getMonth() === viewMonth) {
        const day = d.getDate();
        if (!map[day]) map[day] = [];
        map[day].push(ev);
      }
    }
    return map;
  }, [calendar, viewYear, viewMonth]);

  return (
    <ProductShell>
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="eyebrow">Calendar</p>
            <h1 className="mt-1.5 text-3xl font-semibold tracking-[-0.04em]">Publishing loop</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                const d = new Date(viewYear, viewMonth - 1);
                setViewYear(d.getFullYear());
                setViewMonth(d.getMonth());
              }}
              className="rounded-lg border p-2 text-muted-foreground hover:bg-muted active:scale-[0.97] transition-all"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="min-w-[140px] text-center text-sm font-semibold text-foreground">{monthLabel}</span>
            <button
              onClick={() => {
                const d = new Date(viewYear, viewMonth + 1);
                setViewYear(d.getFullYear());
                setViewMonth(d.getMonth());
              }}
              className="rounded-lg border p-2 text-muted-foreground hover:bg-muted active:scale-[0.97] transition-all"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* Summary chips */}
        <div className="flex flex-wrap gap-2">
          {(["scheduled", "published"] as const).map((status) => {
            const count = calendar.filter((e) => e.status === status).length;
            return (
              <div
                key={status}
                className="flex items-center gap-2 rounded-full border px-3 py-1.5"
                style={{ background: "var(--card)" }}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: STATUS_COLORS[status]?.text }}
                />
                <span className="text-xs font-medium text-foreground capitalize">{status}</span>
                <span className="text-xs text-muted-foreground">{count}</span>
              </div>
            );
          })}
        </div>

        {/* Calendar grid */}
        <div
          className="rounded-xl border overflow-hidden"
          style={{ background: "var(--card)" }}
        >
          {/* DOW headers */}
          <div className="grid grid-cols-7 border-b">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <div
                key={d}
                className="px-2 py-2.5 text-center text-[11px] font-semibold uppercase tracking-wider text-muted-foreground"
              >
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7">
            {Array.from({ length: totalCells }).map((_, cellIdx) => {
              const dayNum = cellIdx - firstDay + 1;
              const isValid = dayNum >= 1 && dayNum <= daysInMonth;
              const isToday =
                isValid &&
                dayNum === today.getDate() &&
                viewMonth === today.getMonth() &&
                viewYear === today.getFullYear();
              const events = isValid ? (eventsByDay[dayNum] ?? []) : [];

              return (
                <div
                  key={cellIdx}
                  className="min-h-[90px] border-r border-b p-1.5 last:border-r-0 transition-colors"
                  style={{
                    background: isValid ? "transparent" : "var(--muted)/30",
                    opacity: isValid ? 1 : 0.4,
                  }}
                >
                  {isValid && (
                    <>
                      <div
                        className={`mb-1 h-6 w-6 flex items-center justify-center rounded-full text-xs font-medium ${
                          isToday ? "text-white" : "text-muted-foreground"
                        }`}
                        style={isToday ? { background: "var(--bronze)" } : undefined}
                      >
                        {dayNum}
                      </div>
                      <div className="space-y-1">
                        {events.slice(0, 2).map((ev) => (
                          <button
                            key={ev.id}
                            onClick={() => setSelectedEvent(ev)}
                            className="w-full truncate rounded px-1.5 py-0.5 text-left text-[10px] font-medium transition-opacity hover:opacity-80 active:scale-[0.97]"
                            style={{
                              background:
                                PLATFORM_COLORS[ev.platform] ?? "rgba(150,165,145,0.7)",
                              color: "#fff",
                            }}
                          >
                            {ev.title}
                          </button>
                        ))}
                        {events.length > 2 && (
                          <p className="text-[9px] text-muted-foreground pl-1">+{events.length - 2} more</p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Event detail panel */}
        {selectedEvent && (
          <div
            className="rounded-xl border p-5"
            style={{ background: "var(--card)" }}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className="h-3 w-3 flex-shrink-0 rounded-full"
                  style={{ background: PLATFORM_COLORS[selectedEvent.platform] ?? "var(--bronze)" }}
                />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground truncate">{selectedEvent.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Clock size={11} className="text-muted-foreground" />
                    <p className="text-xs text-muted-foreground">
                      {new Date(selectedEvent.starts_at).toLocaleDateString(undefined, {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                    <span
                      className="text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize"
                      style={{
                        background: STATUS_COLORS[selectedEvent.status]?.bg,
                        color: STATUS_COLORS[selectedEvent.status]?.text,
                      }}
                    >
                      {selectedEvent.status}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {selectedEvent.status === "scheduled" && (
                  <button
                    onClick={() => {
                      void product.cancelSchedule(selectedEvent.id);
                      setSelectedEvent(null);
                    }}
                    className="rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all active:scale-[0.97]"
                  >
                    Cancel schedule
                  </button>
                )}
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-all"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
            <div
              className="mt-4 rounded-lg p-4 text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed"
              style={{ background: "var(--muted)" }}
            >
              {selectedEvent.content}
            </div>
          </div>
        )}
      </div>
    </ProductShell>
  );
}
