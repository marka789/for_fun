"use client";

import { useState } from "react";

export function CopyButton({ value, label }: { value: string; label: string }) {
  const [done, setDone] = useState(false);

  return (
    <button
      type="button"
      className="button button-ghost"
      onClick={async () => {
        await navigator.clipboard.writeText(value);
        setDone(true);
        window.setTimeout(() => setDone(false), 1600);
      }}
    >
      {done ? "複製咗" : label}
    </button>
  );
}
