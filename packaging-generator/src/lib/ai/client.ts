import { createAnthropic } from "@ai-sdk/anthropic";

const anthropic = createAnthropic({
  baseURL: process.env.AI_BASE_URL,
  apiKey: process.env.AI_API_KEY,
});

export const aiModel = anthropic(process.env.AI_MODEL ?? "claude-opus-4-8");
