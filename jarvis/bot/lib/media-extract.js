/**
 * Извлечение содержимого из форматов, которые Claude Code Read не умеет читать сам:
 * .docx/.pptx/.xlsx (бинарный OOXML-zip) и видео (звук + кадры).
 */

import { spawnSync } from "node:child_process";
import { readFileSync, unlinkSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import ffmpegPath from "ffmpeg-static";
import JSZip from "jszip";
import mammoth from "mammoth";

const MAX_OFFICE_TEXT_CHARS = 8000;

export function isOfficeDoc(ext) {
  return [".docx", ".pptx", ".xlsx"].includes(ext.toLowerCase());
}

async function extractDocx(filePath) {
  const { value } = await mammoth.extractRawText({ path: filePath });
  return value.trim();
}

async function extractPptx(filePath) {
  const data = readFileSync(filePath);
  const zip = await JSZip.loadAsync(data);
  const slideFiles = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name))
    .sort((a, b) => {
      const na = parseInt(a.match(/slide(\d+)\.xml/)[1], 10);
      const nb = parseInt(b.match(/slide(\d+)\.xml/)[1], 10);
      return na - nb;
    });

  const slides = [];
  for (const name of slideFiles) {
    const xml = await zip.files[name].async("string");
    const texts = [...xml.matchAll(/<a:t>([^<]*)<\/a:t>/g)].map((m) => m[1]);
    slides.push(texts.join(" ").trim());
  }
  return slides
    .map((text, i) => `--- Слайд ${i + 1} ---\n${text || "(без текста)"}`)
    .join("\n\n");
}

async function extractXlsx(filePath) {
  const data = readFileSync(filePath);
  const zip = await JSZip.loadAsync(data);

  let sharedStrings = [];
  const sharedFile = zip.files["xl/sharedStrings.xml"];
  if (sharedFile) {
    const xml = await sharedFile.async("string");
    sharedStrings = [...xml.matchAll(/<t[^>]*>([^<]*)<\/t>/g)].map((m) => m[1]);
  }

  const sheetFiles = Object.keys(zip.files)
    .filter((name) => /^xl\/worksheets\/sheet\d+\.xml$/.test(name))
    .sort();

  const sheets = [];
  for (const name of sheetFiles) {
    const xml = await zip.files[name].async("string");
    const rows = [...xml.matchAll(/<row[^>]*>([\s\S]*?)<\/row>/g)].map((rowMatch) => {
      const cells = [...rowMatch[1].matchAll(/<c\b([^>]*?)(?:\/>|>(?:<v>([^<]*)<\/v>)?<\/c>)/g)];
      return cells
        .map(([, attrs, val]) =>
          val === undefined ? "" : /\bt="s"/.test(attrs) ? sharedStrings[val] ?? "" : val
        )
        .join("\t");
    });
    sheets.push(rows.join("\n"));
  }
  return sheets.join("\n\n");
}

export async function extractOfficeText(filePath, ext) {
  let text = "";
  switch (ext.toLowerCase()) {
    case ".docx": text = await extractDocx(filePath); break;
    case ".pptx": text = await extractPptx(filePath); break;
    case ".xlsx": text = await extractXlsx(filePath); break;
    default: return null;
  }
  if (!text) return "";
  return text.length > MAX_OFFICE_TEXT_CHARS
    ? text.slice(0, MAX_OFFICE_TEXT_CHARS) + "\n...(обрезано)"
    : text;
}

// ─── ВИДЕО: звук + кадры ─────────────────────────────────────────────────────

function runFfmpeg(args) {
  const res = spawnSync(ffmpegPath, args, { timeout: 60000 });
  return res.status === 0;
}

export function extractVideoAudio(videoPath) {
  const audioPath = videoPath.replace(/\.\w+$/, "") + "_audio.ogg";
  const ok = runFfmpeg(["-y", "-i", videoPath, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libvorbis", audioPath]);
  return ok && existsSync(audioPath) ? audioPath : null;
}

export function extractVideoFrames(videoPath, count = 2) {
  const dir = dirname(videoPath);
  const base = videoPath.replace(/\.\w+$/, "");
  const frames = [];

  // Кадр 1: ffmpeg сам выбирает наиболее "представительный" кадр
  const frame1 = `${base}_frame1.jpg`;
  if (runFfmpeg(["-y", "-i", videoPath, "-vf", "thumbnail,scale=640:-1", "-frames:v", "1", frame1]) && existsSync(frame1)) {
    frames.push(frame1);
  }

  if (count > 1) {
    // Кадр 2: фиксированная отметка в начале — даёт другой ракурс на ролик
    const frame2 = `${base}_frame2.jpg`;
    if (runFfmpeg(["-y", "-ss", "00:00:02", "-i", videoPath, "-frames:v", "1", frame2]) && existsSync(frame2)) {
      frames.push(frame2);
    }
  }

  return frames;
}

export function cleanupTempFiles(paths) {
  for (const p of paths) {
    try { unlinkSync(p); } catch {}
  }
}
