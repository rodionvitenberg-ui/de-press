import { DialogueClient } from "./DialogueClient";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function DialoguePage({ params }: PageProps) {
  const { id } = await params;
  return <DialogueClient dialogueId={id} />;
}
