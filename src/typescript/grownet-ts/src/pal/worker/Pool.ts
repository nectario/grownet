import { Worker } from 'node:worker_threads';

export class WorkerPool {
  private maxWorkers: number;
  private workers: Array<Worker> = [];
  private idle: Array<Worker> = [];
  private queue: Array<{ task: any; transferList: Array<ArrayBuffer>; resolve: (v: any) => void; reject: (e: Error) => void } > = [];
  private shuttingDown: boolean = false;

  constructor(maxWorkers: number) {
    this.maxWorkers = Math.max(1, maxWorkers);
  }

  static instance: WorkerPool | undefined;

  static getInstance(maxWorkers: number): WorkerPool {
    if (!WorkerPool.instance) WorkerPool.instance = new WorkerPool(maxWorkers);
    return WorkerPool.instance;
  }

  async run(task: any, transferList?: Array<ArrayBuffer>): Promise<any> {
    if (this.shuttingDown) throw new Error('WorkerPool is shutting down');
    const transfer = transferList ?? [];
    return new Promise((resolve, reject) => {
      const job = { task, transferList: transfer, resolve, reject };
      const worker = this.acquire();
      if (worker) this.dispatch(worker, job);
      else this.queue.push(job);
    });
  }

  async close(): Promise<void> {
    this.shuttingDown = true;
    const tasks: Array<Promise<number>> = [];
    for (let index = 0; index < this.workers.length; index += 1) tasks.push(this.workers[index].terminate());
    await Promise.all(tasks);
    this.workers = [];
    this.idle = [];
    this.queue = [];
    WorkerPool.instance = undefined;
  }

  private spawn(): Worker {
    const workerUrl = new URL('./numericWorker.js', import.meta.url);
    const worker = new Worker(workerUrl, { type: 'module' });
    this.workers.push(worker);
    return worker;
  }

  private acquire(): Worker | undefined {
    if (this.idle.length > 0) return this.idle.pop();
    if (this.workers.length < this.maxWorkers) return this.spawn();
    return undefined;
  }

  private release(worker: Worker) {
    if (this.shuttingDown) {
      worker.terminate();
      return;
    }
    const next = this.queue.shift();
    if (next) this.dispatch(worker, next);
    else this.idle.push(worker);
  }

  private dispatch(worker: Worker, job: { task: any; transferList: Array<ArrayBuffer>; resolve: (v: any) => void; reject: (e: Error) => void }) {
    const onMessage = (message: any) => {
      worker.removeListener('message', onMessage);
      worker.removeListener('error', onError);
      job.resolve(message);
      this.release(worker);
    };
    const onError = (err: Error) => {
      worker.removeListener('message', onMessage);
      worker.removeListener('error', onError);
      job.reject(err);
      this.release(worker);
    };
    worker.once('message', onMessage);
    worker.once('error', onError);
    worker.postMessage(job.task, job.transferList);
  }
}

