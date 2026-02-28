import fs from "node:fs";
import path from "node:path";

import { AUTH_STATE_PATH, CREDENTIALS_PATH } from "./constants";
import type { AuthCredentials } from "./types";

export function ensureAuthDir() {
  const authDir = path.dirname(path.join(process.cwd(), AUTH_STATE_PATH));
  fs.mkdirSync(authDir, { recursive: true });
}

export function saveCredentials(credentials: AuthCredentials) {
  ensureAuthDir();
  fs.writeFileSync(path.join(process.cwd(), CREDENTIALS_PATH), JSON.stringify(credentials, null, 2), "utf8");
}

export function loadCredentials(): AuthCredentials {
  const raw = fs.readFileSync(path.join(process.cwd(), CREDENTIALS_PATH), "utf8");
  return JSON.parse(raw) as AuthCredentials;
}

export function randomSuffix() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
