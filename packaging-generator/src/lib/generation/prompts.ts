import type { Brief } from "../onboarding/questions";
import type { StageId } from "./stages";

export function buildSystemPrompt(): string {
  return [
    "Ты — опытный маркетолог-копирайтер, который упаковывает экспертов",
    "(психологов, коучей, наставников). Пишешь сильно, по-человечески, без",
    "канцелярита и без инфоцыганских клише. Отвечаешь только на русском языке.",
    "Возвращаешь готовый текст без вступлений вроде «Вот ваш текст».",
  ].join(" ");
}

function briefBlock(brief: Brief): string {
  return [
    `Ниша: ${brief.niche}`,
    `Аудитория: ${brief.audience}`,
    `Результат клиента: ${brief.result}`,
    `Метод: ${brief.method}`,
    `Отличие: ${brief.difference}`,
    `Продукт и цена: ${brief.product}`,
    `Тон общения: ${brief.tone}`,
  ].join("\n");
}

interface StageOptions {
  acceptedOffer?: string;
  acceptedLanding?: string;
  modifier?: string;
}

const TASKS: Record<StageId, string> = {
  offer:
    "Собери сильный оффер/позиционирование: кто эксперт, для кого, какой результат, чем отличается. 3–5 предложений, выдержи указанный тон.",
  landing:
    "Напиши текст лендинга/профиля на основе принятого оффера: заголовок, блок «о мне», услуги, отзыв-пример, призыв к действию.",
  emails:
    "Напиши серию из 4 писем-прогрева, которые ведут к покупке: у каждого письма тема и короткий текст. Письма опираются на оффер и лендинг.",
};

export function buildStagePrompt(
  stage: StageId,
  brief: Brief,
  options: StageOptions = {},
): string {
  const parts = [briefBlock(brief), "", `Задача: ${TASKS[stage]}`];

  if (stage !== "offer" && options.acceptedOffer) {
    parts.push("", `Принятый оффер:\n${options.acceptedOffer}`);
  }
  if (stage === "emails" && options.acceptedLanding) {
    parts.push("", `Текст лендинга:\n${options.acceptedLanding}`);
  }
  if (options.modifier) {
    parts.push("", `Дополнительно: ${options.modifier}`);
  }

  return parts.join("\n");
}
