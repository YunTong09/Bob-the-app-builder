type Props = {
  kind: "folder" | "investigate" | "rage";
  label: string;
  className?: string;
};

// Animated PNG preserves transparency without depending on video codec support.
// The native picture media query swaps in a still for reduced-motion settings.
export default function PixelAnimation({ kind, label, className = "" }: Props) {
  return (
    <figure className={"pixel-animation " + className} aria-label={label}>
      <picture>
        <source media="(prefers-reduced-motion: reduce)" srcSet={"/animations/" + kind + "-still.png"} />
        {/* Native img is intentional: Next image optimisation would flatten APNG. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={"/animations/" + kind + "-inline.png"} alt="" aria-hidden="true" decoding="async" />
      </picture>
      <figcaption>{label}</figcaption>
    </figure>
  );
}
