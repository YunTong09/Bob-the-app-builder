// Shared by the server layout (init script) and the client settings control.

export const FONT_SIZES = [
  { value: "small", label: "Small" },
  { value: "medium", label: "Default" },
  { value: "large", label: "Large" },
  { value: "x-large", label: "Extra large" },
] as const;

export type FontSize = (typeof FONT_SIZES)[number]["value"];

export const fontSizeStorageKey = "rage-to-reply.font-size";

export const isFontSize = (value: unknown): value is FontSize =>
  FONT_SIZES.some((size) => size.value === value);

// Runs before hydration so the saved size applies without a flash of default-sized text.
export const fontSizeInitScript = `try{var s=localStorage.getItem(${JSON.stringify(fontSizeStorageKey)});if(${JSON.stringify(
  FONT_SIZES.map((size) => size.value),
)}.indexOf(s)>-1)document.documentElement.dataset.fontSize=s}catch(e){}`;
