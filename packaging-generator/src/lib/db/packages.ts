import { Pool } from "pg";
import type { Brief } from "../onboarding/questions";

let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) pool = new Pool({ connectionString: process.env.DATABASE_URL });
  return pool;
}

export interface PackageRow {
  session_id: string;
  brief: Brief;
  materials: Record<string, unknown>;
  created_at: Date;
}

export interface Package {
  sessionId: string;
  brief: Brief;
  materials: Record<string, unknown>;
  createdAt: string;
}

export function rowToPackage(row: PackageRow): Package {
  return {
    sessionId: row.session_id,
    brief: row.brief,
    materials: row.materials,
    createdAt: row.created_at.toISOString(),
  };
}

export async function savePackage(
  sessionId: string,
  brief: Brief,
  materials: Record<string, unknown>,
): Promise<void> {
  await getPool().query(
    `INSERT INTO packages (session_id, brief, materials)
     VALUES ($1, $2, $3)
     ON CONFLICT (session_id)
     DO UPDATE SET brief = $2, materials = $3, created_at = now()`,
    [sessionId, brief, materials],
  );
}

export async function getPackage(sessionId: string): Promise<Package | null> {
  const { rows } = await getPool().query<PackageRow>(
    "SELECT * FROM packages WHERE session_id = $1",
    [sessionId],
  );
  return rows[0] ? rowToPackage(rows[0]) : null;
}
