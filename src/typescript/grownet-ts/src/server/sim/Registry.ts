import { Region } from '../../Region.js';

export class RegionRegistry {
  private static _instance: RegionRegistry | null = null;
  static get instance(): RegionRegistry {
    if (!RegionRegistry._instance) RegionRegistry._instance = new RegionRegistry();
    return RegionRegistry._instance;
  }

  private regions: Map<string, Region> = new Map();
  private counter = 0;

  create(name?: string): { regionId: string; region: Region } {
    const id = `R${this.counter++}`;
    const region = new Region(name ?? id);
    this.regions.set(id, region);
    return { regionId: id, region };
  }

  get(id: string): Region | undefined { return this.regions.get(id); }
  destroy(id: string): boolean { return this.regions.delete(id); }
  listIds(): string[] { return Array.from(this.regions.keys()); }
}

