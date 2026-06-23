import { savePackage, getPackage } from "@/lib/db/packages";
import type { Brief } from "@/lib/onboarding/questions";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { sessionId, brief, materials } = (await req.json()) as {
    sessionId: string;
    brief: Brief;
    materials: Record<string, unknown>;
  };
  await savePackage(sessionId, brief, materials);
  return Response.json({ ok: true });
}

export async function GET(req: Request) {
  const sessionId = new URL(req.url).searchParams.get("sessionId");
  if (!sessionId) return Response.json({ error: "no sessionId" }, { status: 400 });
  const pkg = await getPackage(sessionId);
  return Response.json(pkg);
}
