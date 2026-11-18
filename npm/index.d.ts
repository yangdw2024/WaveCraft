import type { ChildProcess } from "child_process";

export interface LaunchOptions {
  port?: number;
  noOpen?: boolean;
}

export function launchWaveCraft(options?: LaunchOptions): ChildProcess;
