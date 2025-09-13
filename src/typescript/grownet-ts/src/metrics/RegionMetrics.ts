export class RegionMetrics {
  private deliveredEvents: number;
  private totalSlots: number;
  private totalSynapses: number;
  private activePixels: number;
  private centroidRow: number;
  private centroidCol: number;
  private bboxRowMin: number;
  private bboxRowMax: number;
  private bboxColMin: number;
  private bboxColMax: number;

  constructor(
    deliveredEvents: number,
    totalSlots: number,
    totalSynapses: number,
    activePixels: number,
    centroidRow: number,
    centroidCol: number,
    bboxRowMin: number,
    bboxRowMax: number,
    bboxColMin: number,
    bboxColMax: number,
  ) {
    this.deliveredEvents = deliveredEvents;
    this.totalSlots = totalSlots;
    this.totalSynapses = totalSynapses;
    this.activePixels = activePixels;
    this.centroidRow = centroidRow;
    this.centroidCol = centroidCol;
    this.bboxRowMin = bboxRowMin;
    this.bboxRowMax = bboxRowMax;
    this.bboxColMin = bboxColMin;
    this.bboxColMax = bboxColMax;
  }

  getDeliveredEvents(): number { return this.deliveredEvents; }
  getTotalSlots(): number { return this.totalSlots; }
  getTotalSynapses(): number { return this.totalSynapses; }
  getActivePixels(): number { return this.activePixels; }
  getCentroidRow(): number { return this.centroidRow; }
  getCentroidCol(): number { return this.centroidCol; }
  getBboxRowMin(): number { return this.bboxRowMin; }
  getBboxRowMax(): number { return this.bboxRowMax; }
  getBboxColMin(): number { return this.bboxColMin; }
  getBboxColMax(): number { return this.bboxColMax; }
}
export class RegionMetrics {
