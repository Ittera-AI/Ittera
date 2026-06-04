"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type TimeSeriesPoint = {
  date: string;
  value: number;
  posts_count: number;
  ma7?: number | null;
  ma30?: number | null;
};

type TimeSeriesChartProps = {
  data: TimeSeriesPoint[];
  metric: "engagement_rate" | "likes" | "posts" | "impressions";
  interval?: "day" | "week" | "month";
  showMovingAverage?: boolean;
  height?: number;
};

const metricLabels: Record<string, string> = {
  engagement_rate: "Engagement Rate",
  likes: "Total Likes",
  posts: "Posts Published",
  impressions: "Impressions",
};

const metricFormats: Record<string, (value: number) => string> = {
  engagement_rate: (v) => `${(v * 100).toFixed(2)}%`,
  likes: (v) => v.toLocaleString(),
  posts: (v) => v.toString(),
  impressions: (v) => v.toLocaleString(),
};

export function TimeSeriesChart({
  data,
  metric,
  interval = "day",
  showMovingAverage = true,
  height = 300,
}: TimeSeriesChartProps) {
  const formattedData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      formattedDate: formatDate(point.date, interval),
      formattedValue: metricFormats[metric](point.value),
    }));
  }, [data, metric, interval]);

  const yAxisDomain = useMemo(() => {
    const values = data.map((d) => d.value);
    const min = Math.min(...values, 0);
    const max = Math.max(...values, 0);
    const padding = (max - min) * 0.1;
    return [Math.max(0, min - padding), max + padding];
  }, [data]);

  const hasMovingAverage = useMemo(() => {
    return showMovingAverage && data.some((d) => d.ma7 || d.ma30);
  }, [data, showMovingAverage]);

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border bg-muted/30"
        style={{ height }}
      >
        <p className="text-sm text-muted-foreground">No data available</p>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={formattedData}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor="var(--bronze)"
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor="var(--bronze)"
                stopOpacity={0}
              />
            </linearGradient>
            <linearGradient id="colorMA7" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor="var(--olive)"
                stopOpacity={0.1}
              />
              <stop
                offset="95%"
                stopColor="var(--olive)"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--muted)"
            opacity={0.5}
          />
          <XAxis
            dataKey="formattedDate"
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--muted)", strokeWidth: 1 }}
            minTickGap={30}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            tickLine={false}
            axisLine={false}
            domain={yAxisDomain}
            tickFormatter={metricFormats[metric]}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || payload.length === 0) return null;
              const point = payload[0].payload as TimeSeriesPoint & {
                formattedDate: string;
              };
              return (
                <div className="rounded-lg border bg-popover p-3 shadow-md">
                  <p className="text-xs font-medium text-popover-foreground mb-2">
                    {point.formattedDate}
                  </p>
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-xs text-muted-foreground">
                        {metricLabels[metric]}
                      </span>
                      <span
                        className="text-xs font-semibold"
                        style={{ color: "var(--bronze)" }}
                      >
                        {metricFormats[metric](point.value)}
                      </span>
                    </div>
                    {point.posts_count > 0 && (
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-xs text-muted-foreground">
                          Posts
                        </span>
                        <span className="text-xs font-medium">
                          {point.posts_count}
                        </span>
                      </div>
                    )}
                    {point.ma7 && (
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-xs text-muted-foreground">
                          7-day MA
                        </span>
                        <span
                          className="text-xs font-medium"
                          style={{ color: "var(--olive)" }}
                        >
                          {metricFormats[metric](point.ma7)}
                        </span>
                      </div>
                    )}
                    {point.ma30 && (
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-xs text-muted-foreground">
                          30-day MA
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">
                          {metricFormats[metric](point.ma30)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="var(--bronze)"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorValue)"
            name={metricLabels[metric]}
          />
          {hasMovingAverage && (
            <Area
              type="monotone"
              dataKey="ma7"
              stroke="var(--olive)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              fill="url(#colorMA7)"
              name="7-day MA"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function formatDate(
  dateStr: string,
  interval: "day" | "week" | "month"
): string {
  const date = new Date(dateStr);

  switch (interval) {
    case "day":
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    case "week":
      return `Week of ${date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      })}`;
    case "month":
      return date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });
    default:
      return dateStr;
  }
}

export default TimeSeriesChart;
