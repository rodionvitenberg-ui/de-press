import { getMessages, type Locale } from "@/lib/i18n";

/** Fixed Story Topic labels (mirrors backend StoryTopic + i18n catalogs). */
export function topicLabel(
  topic: string | null | undefined,
  locale: Locale = "ru",
): string {
  if (!topic) return "";
  const labels = getMessages(locale).topics;
  return labels[topic] ?? topic;
}
