"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Clock, X } from "lucide-react";
import { AuthenticatedImage } from "@/components/product/AuthenticatedImage";
import { ProductShell } from "@/components/product/ProductShell";
import { useProduct } from "@/hooks/useProduct";

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: "rgba(163,138,112,0.85)",
  twitter: "rgba(150,165,145,0.85)",
  instagram: "rgba(196,168,130,0.85)",
};

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  scheduled: { bg: "rgba(163,138,112,0.18)", text: "var(--bronze)" },
  publishing: { bg: "rgba(163,138,112,0.18)", text: "var(--bronze)" },
  published: { bg: "rgba(150,165,145,0.18)", text: "var(--olive)" },
  failed: { bg: "rgba(180,83,9,0.14)", text: "rgb(180,83,9)" },
  cancelled: { bg: "var(--muted)", text: "var(--text-muted)" },
  review_due: { bg: "rgba(196,168,130,0.18)", text: "var(--bronze)" },
  approved: { bg: "rgba(150,165,145,0.18)", text: "var(--olive)" },
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
  const searchParams = useSearchParams();
  const calendar = product.calendar;
  const loadCalendar = product.loadCalendar;
  const [selectedEvent, setSelectedEvent] = useState<(typeof calendar)[0] | null>(null);

  const today = useMemo(() => new Date(), []);
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  useEffect(() => {
    void loadCalendar().catch(() => undefined);
  }, [loadCalendar]);

  useEffect(() => {
    const reviewId = searchParams.get("review");
    if (!reviewId || !calendar.length) return;
    const event = calendar.find((item) => item.id === reviewId);
    if (event) {
      const timer = window.setTimeout(() => {
        setSelectedEvent(event);
        const starts = new Date(event.starts_at);
        setViewYear(starts.getFullYear());
        setViewMonth(starts.getMonth());
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [calendar, searchParams]);

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
          {(["scheduled", "review_due", "publishing", "published", "failed", "cancelled"] as const).map((status) => {
            const count = status === "review_due"
              ? calendar.filter((e) => e.review_status === "review_due").length
              : calendar.filter((e) => e.status === status).length;
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
                <span className="text-xs font-medium text-foreground capitalize">{status.replace("_", " ")}</span>
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
          <div className="rounded-xl border p-5" style={{ background: "var(--card)" }}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex min-w-0 items-center gap-3">
                <span
                  className="h-3 w-3 flex-shrink-0 rounded-full"
                  style={{ background: PLATFORM_COLORS[selectedEvent.platform] ?? "var(--bronze)" }}
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-foreground">{selectedEvent.title}</p>
                  <div className="mt-0.5 flex flex-wrap items-center gap-2">
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
                        {([selectedEvent.status, selectedEvent.review_status].filter(Boolean) as string[]).map((statusLabel) => (
                      <span
                        key={statusLabel}
                        className="rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize"
                        style={{
                          background: STATUS_COLORS[statusLabel]?.bg ?? "var(--muted)",
                          color: STATUS_COLORS[statusLabel]?.text ?? "var(--text-muted)",
                        }}
                      >
                        {statusLabel.replace("_", " ")}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex flex-shrink-0 flex-wrap items-center gap-2">
                {selectedEvent.status === "scheduled" && selectedEvent.review_status !== "approved" ? (
                  <button
                    onClick={() => void product.approveDraft(selectedEvent.id)}
                    className="rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97]"
                  >
                    Approve
                  </button>
                ) : null}
                {selectedEvent.status === "scheduled" || selectedEvent.status === "failed" ? (
                  <>
                    <button
                      onClick={() => void product.publish(selectedEvent.id)}
                      className="rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97]"
                    >
                      Publish now
                    </button>
                    {selectedEvent.status === "scheduled" ? (
                      <button
                        onClick={() => {
                          void product.cancelSchedule(selectedEvent.id);
                          setSelectedEvent(null);
                        }}
                        className="rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:bg-muted hover:text-foreground active:scale-[0.97]"
                      >
                        Cancel schedule
                      </button>
                    ) : null}
                  </>
                ) : null}
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="rounded-lg p-1.5 text-muted-foreground transition-all hover:bg-muted"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
            {selectedEvent.media?.length ? (
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {selectedEvent.media.map((media) => (
                  media.preview_url ? (
                    <AuthenticatedImage
                      key={media.id}
                      mediaId={media.id}
                      fallbackSrc={media.preview_url}
                      alt={media.filename}
                      className="aspect-video rounded-lg border object-cover"
                    />
                  ) : null
                ))}
              </div>
            ) : null}
            {selectedEvent.platform === "linkedin" && (selectedEvent.media?.length ?? 0) > 1 ? (
              <p className="mt-3 text-xs text-destructive">
                LinkedIn publishing currently supports 1 image per post. Remove extra images before scheduling or publishing.
              </p>
            ) : null}
            <div
              className="mt-4 rounded-lg p-4 text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed"
              style={{ background: "var(--muted)" }}
            >
              {selectedEvent.content}
            </div>
            {product.error ? <p className="mt-3 text-xs text-destructive">{product.error}</p> : null}
          </div>
        )}
      </div>
    </ProductShell>
  );
}
