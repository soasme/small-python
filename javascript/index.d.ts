/** A value that converts to an engine value. */
export type PyValue =
  | null | undefined | boolean | number | bigint | string | Uint8Array | Complex | PyObject
  | PyValue[] | Set<PyValue> | Map<PyValue, PyValue> | { [key: string]: PyValue }
  | ((...args: any[]) => unknown);

export interface RuntimeOptions {
  /** Register the standard modules (sys, gc, weakref). Default true. */
  std?: boolean;
  /** Evaluation steps per top-level eval or exec; 0 is unlimited. */
  stepLimit?: number;
  /** Bytes the engine may hold; 0 is unlimited. */
  memoryLimit?: number;
  /** Milliseconds one operation may run in the worker. */
  timeout?: number;
  /** Receives printed text; by default lines go to console.log. */
  output?: (text: string) => void | Promise<void>;
  /** Maps a module name to its source, or null. */
  loader?: (name: string) => string | null | undefined | Promise<string | null | undefined>;
  /** Largest message between the runtime and its worker, in bytes. */
  messageLimit?: number;
}

export class Runtime {
  static create(options?: RuntimeOptions): Promise<Runtime>;
  private constructor();
  readonly version: string;
  readonly closed: boolean;
  eval(source: string, filename?: string): Promise<any>;
  exec(source: string, filename?: string): Promise<void>;
  call(target: string | PyObject, args?: PyValue[], kwargs?: { [key: string]: PyValue } | Map<string, PyValue>): Promise<any>;
  get(name: string): Promise<any>;
  set(name: string, value: PyValue): Promise<void>;
  delete(name: string): Promise<void>;
  define<F extends (...args: any[]) => unknown>(name: string, fn: F): Promise<F>;
  registerModule(name: string, members?: { [key: string]: PyValue } | Map<string, PyValue> | null, source?: string | null): Promise<void>;
  collect(): Promise<number>;
  close(): void;
  [Symbol.dispose](): void;
}

export class PyObject {
  private constructor();
  get(name: string): Promise<any>;
  set(name: string, value: PyValue): Promise<void>;
  getItem(key: PyValue): Promise<any>;
  setItem(key: PyValue, value: PyValue): Promise<void>;
  len(): Promise<number>;
  has(item: PyValue): Promise<boolean>;
  call(args?: PyValue[], kwargs?: { [key: string]: PyValue } | Map<string, PyValue>): Promise<any>;
  bool(): Promise<boolean>;
  hash(): Promise<number | bigint>;
  compare(op: "<" | "<=" | "==" | "!=" | ">" | ">=", other: PyValue): Promise<any>;
  repr(): Promise<string>;
  str(): Promise<string>;
  dir(): Promise<string[]>;
  [Symbol.asyncIterator](): AsyncIterator<any>;
  release(): void;
}

export class Complex {
  constructor(real: number, imag: number);
  readonly real: number;
  readonly imag: number;
}

/** Mark a host function as taking keyword arguments: fn(...args, kwargs). */
export function keywords<F extends (...args: any[]) => unknown>(fn: F): F;

export class PythonError extends Error {
  readonly type: string;
  readonly exception: PyObject | null;
  readonly filename: string | null;
  readonly lineno: number | null;
}

export class WorkerError extends Error {
  readonly returncode: number | null;
}

export class Timeout extends WorkerError {}
