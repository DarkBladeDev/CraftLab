import { PaginatedContainerPreset } from "../../../types/presets";

export const overviewTelemetryPreset: PaginatedContainerPreset = {
  id: "overview-telemetry",
  title: "System Telemetry (psutil)",
  category: "system",
  defaultSpan: { cols: 1, rows: 1, minCols: 1, maxCols: 2 },
  paginationMode: "subviews",
  pages: [
    {
      pageId: "cpu-ram",
      title: "Host CPU & RAM",
      badge: "● LIVE",
      badgeColor: "green",
      outputs: [
        {
          type: "metric_stat",
          label: "Host CPU",
          value: (data) => `${data.metrics?.host_cpu_percent ?? "--"}%`,
          progressPercent: (data) => data.metrics?.host_cpu_percent ?? 0,
          color: "blue",
        },
        {
          type: "metric_stat",
          label: "Host RAM",
          value: (data) => `${data.metrics?.host_ram_percent ?? "--"}%`,
          subValue: (data) =>
            data.metrics?.host_ram_used_mb && data.metrics?.host_ram_total_mb
              ? `${data.metrics.host_ram_used_mb} MB / ${data.metrics.host_ram_total_mb} MB`
              : "",
          progressPercent: (data) => data.metrics?.host_ram_percent ?? 0,
          color: "cyan",
        },
      ],
    },
    {
      pageId: "disk-threads",
      title: "Disk Storage & Process Threads",
      badge: "Storage",
      badgeColor: "yellow",
      outputs: [
        {
          type: "gauge",
          label: "Disk Usage",
          percent: (data) => data.metrics?.disk_usage_percent ?? 0,
          displayValue: (data) =>
            data.metrics?.disk_free_gb
              ? `${data.metrics.disk_usage_percent}% (${data.metrics.disk_free_gb} GB free)`
              : `${data.metrics?.disk_usage_percent ?? "--"}%`,
          color: "yellow",
        },
        {
          type: "metric_stat",
          label: "Process Threads",
          value: (data) => `${data.metrics?.process_num_threads ?? "--"}`,
          color: "green",
        },
      ],
    },
    {
      pageId: "process-details",
      title: "Managed Process Footprint",
      badge: (data) => `PID ${data.metrics?.process_pid ?? data.status?.pid ?? "--"}`,
      badgeColor: "purple",
      outputs: [
        {
          type: "key_value",
          label: "Process Memory RSS",
          value: (data) => `${data.metrics?.process_memory_rss_mb ?? data.status?.memory_rss_mb ?? "--"} MB`,
          mono: true,
          statusDot: "cyan",
        },
        {
          type: "key_value",
          label: "Process CPU Usage",
          value: (data) => `${data.metrics?.process_cpu_percent ?? "--"}%`,
          mono: true,
          statusDot: "green",
        },
        {
          type: "key_value",
          label: "Supervisor Status",
          value: (data) => data.status?.status ?? "UNKNOWN",
          mono: true,
          statusDot: "green",
        },
      ],
    },
  ],
};
