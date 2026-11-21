"use client";
import { useEffect, useRef, useState } from "react";
type Props = {
  kind: "folder" | "investigate" | "rage";
  label: string;
  className?: string;
};
export default function PixelAnimation({ kind, label, className = "" }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const [reduced, setReduced] = useState(true);
  useEffect(() => {
    const query = matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (reduced) ref.current?.pause();
    else void ref.current?.play().catch(() => {});
  }, [reduced]);
  return (
    <figure className={"pixel-animation " + className} aria-label={label}>
      <video
        ref={ref}
        src={"/animations/" + kind + ".mp4"}
        muted
        loop
        playsInline
        preload="metadata"
        aria-hidden="true"
      />
      <figcaption>{label}</figcaption>
    </figure>
  );
}
