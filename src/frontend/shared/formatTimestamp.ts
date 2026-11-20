export function formatTimestamp(timestamp: string | null | undefined) {
  // Show the stated local time as supplied; blank when unknown (never invent a date).
  return timestamp ? timestamp.slice(0, 16).replace("T", " ") : "";
}
