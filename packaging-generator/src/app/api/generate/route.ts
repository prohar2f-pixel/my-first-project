import { streamText } from "ai";
import { aiModel } from "@/lib/ai/client";
import { buildSystemPrompt, buildStagePrompt } from "@/lib/generation/prompts";
import type { Brief } from "@/lib/onboarding/questions";
import type { StageId } from "@/lib/generation/stages";

export const runtime = "nodejs";
export const maxDuration = 60;

interface GenerateBody {
  stage: StageId;
  brief: Brief;
  acceptedOffer?: string;
  acceptedLanding?: string;
  modifier?: string;
}

export async function POST(req: Request) {
  const body = (await req.json()) as GenerateBody;

  const result = streamText({
    model: aiModel,
    system: buildSystemPrompt(),
    prompt: buildStagePrompt(body.stage, body.brief, {
      acceptedOffer: body.acceptedOffer,
      acceptedLanding: body.acceptedLanding,
      modifier: body.modifier,
    }),
    maxOutputTokens: body.stage === "emails" ? 4000 : 2000,
  });

  return result.toTextStreamResponse();
}
