/**
 * Run one ingest pass locally against your real Supabase:
 *   cp .env.example .env.local && fill it in
 *   npm run ingest:local
 * Loads .env.local, then runs the same code Vercel Cron calls.
 */
import { readFileSync } from "node:fs";
import { runIngest } from "../lib/ingest";

for (const file of [".env.local", ".env"]) {
  try {
    for (const line of readFileSync(file, "utf8").split("\n")) {
      const m = line.match(/^\s*([\w.]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  } catch {
    /* file optional */
  }
}

runIngest()
  .then((r) => console.log("ingest:", JSON.stringify(r, null, 2)))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
