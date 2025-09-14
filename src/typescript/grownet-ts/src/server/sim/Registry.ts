import { Region } from '../../Region.js';

export class RegionRegistry {
  private static instanceRef: RegionRegistry | null = null;
  static get instance(): RegionRegistry {
    if (!RegionRegistry.instanceRef) RegionRegistry.instanceRef = new RegionRegistry();
    return RegionRegistry.instanceRef;
  }

  private regions: Map<string, Region> = new Map();
  private counter = 0;

  create(name?: string): { regionId: string; region: Region } {
    const regionId = `R${this.counter++}`;
    const region = new Region(name ?? regionId);
    this.regions.set(regionId, region);
    return { regionId, region };
  }

  get(regionIdArg: string): Region | undefined { return this.regions.get(regionIdArg); }
  destroy(regionIdArg: string): boolean { return this.regions.delete(regionIdArg); }
  listIds(): string[] { return Array.from(this.regions.keys()); }
}

