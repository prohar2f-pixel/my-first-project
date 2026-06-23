import { generateObject } from "ai";
import { aiModel } from "@/lib/ai/client";
import {
  EvaluationSchema,
  buildEvaluationPrompt,
} from "@/lib/generation/evaluation";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: Request) {
  const { offer } = (await req.json()) as { offer: string };

  const { object } = await generateObject({
    model: aiModel,
    schema: EvaluationSchema,
    prompt: buildEvaluationPrompt(offer),
  });

  return Response.json(object);
}
