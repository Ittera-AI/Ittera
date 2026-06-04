"use client";

import { useState } from "react";
import { Calendar, ChevronDown } from "lucide-react";

type DateRangeOption =
  | { type: "preset"; value: 7 | 30 | 90 }
  | { type: "custom"; start: Date; end: Date };

type DateRangeSelectorProps = {
  value: number; // Days
  onChange: (days: number) => void;
  disabled?: boolean;
};

const presetOptions = [
  { label: "Last 7 days", value: 7 },
  { label: "Last 30 days", value: 30 },
  { label: "Last 90 days", value: 90 },
];

export function DateRangeSelector({
  value,
  onChange,
  disabled = false,
}: DateRangeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedLabel =
    presetOptions.find((opt) => opt.value === value)?.label || `${value} days`;

  return (
    <div className="relative">
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm font-medium transition-colors hover:bg-muted disabled:opacity-50"
      >
        <Calendar size={14} className="text-muted-foreground" />
        <span>{selectedLabel}</span>
        <ChevronDown
          size={14}
          className={`text-muted-foreground transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-lg border bg-popover p-1 shadow-lg animate-in fade-in slide-in-from-top-2">
            {presetOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-sm transition-colors ${
                  value === option.value
                    ? "bg-primary text-primary-foreground"
                    : "text-popover-foreground hover:bg-muted"
                }`}
              >
                <span>{option.label}</span>
                {value === option.value && (
                  <span className="text-xs opacity-70">Active</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// Compact version for tighter spaces
export function DateRangePills({
  value,
  onChange,
}: DateRangeSelectorProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border bg-card p-1">
      {presetOptions.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            value === option.value
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          {option.value}D
        </button>
      ))}
    </div>
  );
}

export default DateRangeSelector;
