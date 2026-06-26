"use client";

import { useEffect } from "react";

// Подключает тот же WebGL-эффект, что на aiprohar.ru (public/fluid.js).
// Не запускается при prefers-reduced-motion. Глобальный флаг страхует
// от двойного запуска в React StrictMode (dev).
export function FluidBackground() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if ((window as unknown as { __fluidLoaded?: boolean }).__fluidLoaded) return;
    (window as unknown as { __fluidLoaded?: boolean }).__fluidLoaded = true;

    const script = document.createElement("script");
    script.src = "/fluid.js";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  return (
    <canvas
      id="smokeCanvas"
      className="pointer-events-none fixed inset-0 z-0"
      style={{ mixBlendMode: "screen" }}
    />
  );
}
