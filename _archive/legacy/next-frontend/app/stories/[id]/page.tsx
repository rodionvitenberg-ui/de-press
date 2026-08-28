import { StoryDetailClient } from "./StoryDetailClient";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function StoryPage({ params }: PageProps) {
  const { id } = await params;
  return <StoryDetailClient storyId={id} />;
}
