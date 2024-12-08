import { db } from "../db";
import { uploadFromPresignedUrl } from "./uploadFromPresignedUrl";

export const uploadCallRecordingToDB = async (
  callId: string,
  audioUrl: string,
  agentId: string,
  regionId: string,
  createdAt: Date,
) => {
  const { audioUrl: url, duration } = await uploadFromPresignedUrl(
    callId,
    audioUrl,
  );
  return await db.callRecording.upsert({
    where: {
      id: callId,
    },
    create: {
      id: callId,
      audioUrl: url,
      createdAt: createdAt,
      agentId,
      regionId,
      duration,
    },
    update: {},
  });
};