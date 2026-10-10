import { PaginatedContainerPreset } from "../../../types/presets";

export const liveLogStreamPreset: PaginatedContainerPreset = {
  id: "live-log-stream",
  title: "Live Log Stream",
  category: "logs",
  defaultSpan: { cols: 4, rows: 2, minCols: 2, maxCols: 4 },
  paginationMode: "none",
  outputs: [
    {
      type: "log_stream",
      autoscrollDefault: true,
      maxLines: 500,
    },
  ],
};
