import { useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import "./CopilotToolRenderers.css";

type ChartPoint = { label: string; value: number };
type ChartData = {
  title: string;
  chart_type: "bar" | "line" | "pie";
  data: ChartPoint[];
};

const chartParameters = z.object({
  title: z.string(),
  chart_type: z.enum(["bar", "line", "pie"]),
  data: z.array(z.object({ label: z.string(), value: z.number() })),
});

function parseChart(value: unknown): ChartData | null {
  if (typeof value === "string") {
    try {
      return parseChart(JSON.parse(value));
    } catch {
      return null;
    }
  }
  if (!value || typeof value !== "object") return null;

  const parsed = chartParameters.safeParse(value);
  return parsed.success ? parsed.data : null;
}

const colors = [
  "var(--chart-1, var(--primary))",
  "var(--chart-2, var(--primary))",
  "var(--chart-3, var(--primary))",
  "var(--chart-4, var(--primary))",
  "var(--chart-5, var(--primary))",
];

function CartesianChart({ chart }: { chart: ChartData }) {
  const { data, chart_type: type } = chart;
  const minimum = Math.min(0, ...data.map((point) => point.value));
  const maximum = Math.max(0, ...data.map((point) => point.value));
  const range = Math.max(1, maximum - minimum);
  const left = 48;
  const right = 584;
  const top = 24;
  const bottom = 174;
  const slot = (right - left) / data.length;
  const points = data.map((point, index) => ({
    ...point,
    x: left + slot * (index + 0.5),
    y: bottom - ((point.value - minimum) / range) * (bottom - top),
  }));
  const zeroY = bottom - ((0 - minimum) / range) * (bottom - top);

  return (
    <svg className="copilot-chart-svg" viewBox="0 0 600 220" role="img" aria-label={chart.title}>
      <line className="copilot-chart-axis" x1={left} y1={zeroY} x2={right} y2={zeroY} />
      {type === "line" ? (
        <>
          <polyline
            className="copilot-chart-line"
            points={points.map(({ x, y }) => `${x},${y}`).join(" ")}
          />
          {points.map(({ x, y, label, value }, index) => (
            <circle className="copilot-chart-point" key={`${label}-${index}`} cx={x} cy={y} r="4">
              <title>{label}: {value}</title>
            </circle>
          ))}
        </>
      ) : (
        points.map(({ x, y, label, value }, index) => {
          const width = Math.max(4, Math.min(42, slot * 0.62));
          return (
            <g key={`${label}-${index}`}>
              <rect
                x={x - width / 2}
                y={Math.min(y, zeroY)}
                width={width}
                height={Math.max(1, Math.abs(zeroY - y))}
                rx="3"
                fill={colors[index % colors.length]}
              />
              <text className="copilot-chart-value" x={x} y={Math.max(top - 4, y - 7)} textAnchor="middle">
                {value}
              </text>
              <text className="copilot-chart-label" x={x} y="198" textAnchor="middle">
                {label.slice(0, 12)}
              </text>
              <title>{label}: {value}</title>
            </g>
          );
        })
      )}
      {type === "line" && points.map(({ x, label }, index) => (
        <text className="copilot-chart-label" key={`${label}-${index}`} x={x} y="198" textAnchor="middle">
          {label.slice(0, 12)}
        </text>
      ))}
    </svg>
  );
}

function PieChart({ chart }: { chart: ChartData }) {
  const total = chart.data.reduce((sum, point) => sum + Math.max(0, point.value), 0);
  const circumference = 2 * Math.PI * 42;
  let offset = 0;

  if (total <= 0) return null;
  return (
    <div className="copilot-chart-pie">
      <svg viewBox="0 0 100 100" role="img" aria-label={chart.title}>
        {chart.data.map((point, index) => {
          const length = Math.max(0, point.value) / total * circumference;
          const slice = (
            <circle
              key={`${point.label}-${index}`}
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke={colors[index % colors.length]}
              strokeWidth="16"
              strokeDasharray={`${length} ${circumference - length}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 50 50)"
            >
              <title>{point.label}: {point.value}</title>
            </circle>
          );
          offset += length;
          return slice;
        })}
      </svg>
      <ul>
        {chart.data.map((point, index) => (
          <li key={`${point.label}-${index}`}>
            <span style={{ background: colors[index % colors.length] }} />
            {point.label}: {point.value}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChartRenderer({
  chart,
  loading,
  labels,
}: {
  chart: ChartData | null;
  loading: boolean;
  labels: { loading: string; empty: string; title: string };
}) {
  if (!chart) {
    return <div className="copilot-chart-state">{loading ? labels.loading : labels.empty}</div>;
  }
  return (
    <figure className="copilot-chart" aria-busy={loading}>
      <figcaption>{chart.title || labels.title}</figcaption>
      {chart.data.length === 0 ? (
        <div className="copilot-chart-state">{labels.empty}</div>
      ) : chart.chart_type === "pie" ? (
        <PieChart chart={chart} />
      ) : (
        <CartesianChart chart={chart} />
      )}
      {loading && <div className="copilot-chart-state">{labels.loading}</div>}
    </figure>
  );
}

/**
 * Use CopilotKit's built-in renderer for regular calls and its named
 * useRenderTool extension point for the chart returned by render_chart.
 */
export function CopilotToolRenderers() {
  useDefaultRenderTool();

  const { t } = useTranslation();
  const labels = {
    loading: t("chat.chartLoading"),
    empty: t("chat.chartEmpty"),
    title: t("chat.chartTitle"),
  };
  useRenderTool({
    name: "render_chart",
    parameters: chartParameters,
    render: ({ parameters, result, status }) => (
      <ChartRenderer
        chart={parseChart(result) ?? parseChart(parameters)}
        loading={status !== "complete"}
        labels={labels}
      />
    ),
  }, []);

  return null;
}
