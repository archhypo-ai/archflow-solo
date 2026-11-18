import { useDefaultRenderTool, useRenderTool } from "@copilotkit/react-core/v2";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import "./NativeChartTool.css";

type ChartPoint = { label: string; value: number };
type ChartData = { title: string; chart_type: "bar" | "line" | "pie"; data: ChartPoint[] };

function stringify(value: unknown) {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2) ?? "";
  } catch {
    return String(value);
  }
}

function parseObject(value: unknown): Partial<ChartData> | null {
  if (typeof value === "string") {
    try {
      return parseObject(JSON.parse(value));
    } catch {
      return null;
    }
  }
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  if (!Array.isArray(candidate.data)) return null;
  const data = candidate.data.filter((point): point is ChartPoint =>
    !!point && typeof point === "object" &&
    typeof (point as ChartPoint).label === "string" &&
    typeof (point as ChartPoint).value === "number" &&
    Number.isFinite((point as ChartPoint).value));
  return {
    title: typeof candidate.title === "string" ? candidate.title : "Chart",
    chart_type: candidate.chart_type === "line" || candidate.chart_type === "pie"
      ? candidate.chart_type
      : "bar",
    data,
  };
}

function PieChart({ data, labels }: { data: ChartPoint[]; labels: { empty: string; pie: string } }) {
  const total = data.reduce((sum, point) => sum + Math.max(0, point.value), 0);
  if (!total) return <p className="native-chart-empty">{labels.empty}</p>;
  const colors = ["#2563eb", "#0f766e", "#d97706", "#7c3aed", "#db2777", "#0891b2"];
  let offset = 0;
  const circumference = 2 * Math.PI * 42;
  return (
    <div className="native-chart-pie">
      <svg viewBox="0 0 100 100" role="img" aria-label={labels.pie}>
        <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-border)" strokeWidth="16" />
        {data.map((point, index) => {
          const length = Math.max(0, point.value) / total * circumference;
          const circle = (
            <circle key={`${point.label}-${index}`} cx="50" cy="50" r="42" fill="none"
              stroke={colors[index % colors.length]} strokeWidth="16"
              strokeDasharray={`${length} ${circumference - length}`}
              strokeDashoffset={-offset} transform="rotate(-90 50 50)" />
          );
          offset += length;
          return circle;
        })}
      </svg>
      <ul>
        {data.map((point, index) => (
          <li key={`${point.label}-${index}`}>
            <span style={{ backgroundColor: colors[index % colors.length] }} />
            {point.label}: {point.value}
          </li>
        ))}
      </ul>
    </div>
  );
}

function BarChart({ data, line = false, empty }: { data: ChartPoint[]; line?: boolean; empty: string }) {
  if (!data.length) return <p className="native-chart-empty">{empty}</p>;
  const max = Math.max(1, ...data.map(({ value }) => value));
  const colors = ["#2563eb", "#0f766e", "#d97706", "#7c3aed", "#db2777", "#0891b2"];
  const points = data.map((point, index) => ({
    ...point,
    x: 42 + index * (516 / Math.max(data.length - 1, 1)),
    y: 174 - (Math.max(0, point.value) / max) * 140,
  }));
  return (
    <svg className="native-chart-cartesian" viewBox="0 0 600 220" role="img">
      <line x1="36" y1="176" x2="576" y2="176" stroke="var(--color-border-strong)" />
      {line ? (
        <>
          <polyline points={points.map(({ x, y }) => `${x},${y}`).join(" ")}
            fill="none" stroke="var(--color-accent)" strokeWidth="3" />
          {points.map(({ x, y, label, value }, index) => (
            <circle key={`${label}-${index}`} cx={x} cy={y} r="4"
              fill="var(--color-accent)">
              <title>{label}: {value}</title>
            </circle>
          ))}
        </>
        ) : points.map(({ x, y, label, value }, index) => {
          const width = Math.min(42, 420 / points.length);
          return (
            <g key={`${label}-${index}`}>
            <rect x={x - width / 2} y={y} width={width} height={176 - y}
              rx="3" fill={colors[index % colors.length]} />
            <text className="native-chart-value" x={x} y={Math.max(12, y - 6)} textAnchor="middle">{value}</text>
            <text className="native-chart-label" x={x} y="197" textAnchor="middle">{label.slice(0, 12)}</text>
            <title>{label}: {value}</title>
          </g>
        );
      })}
      {line && points.map(({ x, label }, index) => (
        <text key={`${label}-${index}`} x={x} y="197" textAnchor="middle">
          {label.slice(0, 12)}
        </text>
      ))}
    </svg>
  );
}

function ChartCard({
  chart,
  loading,
  labels,
}: {
  chart: Partial<ChartData> | null;
  loading: boolean;
  labels: { empty: string; pie: string; preparing: string; title: string };
}) {
  if (!chart) return <p className="native-chart-empty">{labels.preparing}</p>;
  return (
    <figure className="native-chart-card" aria-busy={loading}>
      <figcaption>{chart.title || labels.title}</figcaption>
      {chart.chart_type === "pie"
        ? <PieChart data={chart.data ?? []} labels={labels} />
        : <BarChart data={chart.data ?? []} line={chart.chart_type === "line"} empty={labels.empty} />}
      {loading && <span className="native-chart-status">{labels.preparing}</span>}
    </figure>
  );
}

export function NativeChartTool() {
  const { t } = useTranslation();
  const labels = {
    empty: t("chat.chartEmpty"),
    pie: t("chat.pieChart"),
    preparing: t("chat.chartPreparing"),
    title: t("chat.chartTitle"),
  };
  useDefaultRenderTool({
    render: ({ name, parameters, status, result }) => {
      if (name === "publish_a2ui_surface") return null;
      return (
        <details className="native-tool-fallback">
          <summary>
            {name.replace(/_/g, " ")} · {t(`chat.toolStatus.${status}`)}
          </summary>
          <div>
            <strong>{t("chat.toolArguments")}</strong>
            <pre>{stringify(parameters)}</pre>
            {result !== undefined && (
              <>
                <strong>{t("chat.toolResult")}</strong>
                <pre>{stringify(result)}</pre>
              </>
            )}
          </div>
        </details>
      );
    },
  }, []);
  useRenderTool({
    name: "render_chart",
    parameters: z.object({
      title: z.string(),
      chart_type: z.enum(["bar", "line", "pie"]),
      data: z.array(z.object({ label: z.string(), value: z.number() })),
    }),
    render: ({ parameters, result, status }) => (
      <ChartCard
        chart={parseObject(result) ?? parseObject(parameters)}
        loading={status !== "complete"}
        labels={labels}
      />
    ),
  }, []);
  return null;
}
