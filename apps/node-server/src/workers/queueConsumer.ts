import { env } from "../env";
import { transcribeAndSaveCall } from "../services/observability";
import { AgentService } from "@repo/services/src/agent";
import { sqs } from "../clients/s3Client";
import { db } from "../db";
import { Semaphore } from "../utils/semaphore";

const agentService = new AgentService(db);

async function processMessage(
  message: { Body?: string; ReceiptHandle?: string },
  queueUrl: string,
) {
  try {
    const data = JSON.parse(message.Body || "{}");
    const {
      callId,
      stereoRecordingUrl,
      agentId,
      createdAt,
      ownerId,
      metadata,
      saveRecording,
      language,
    } = data;
    if (!callId || !stereoRecordingUrl || !ownerId || !createdAt) {
      console.error("Missing required fields in message:", data);
      throw new Error("Missing required fields");
    }

    console.log("PROCESSING CALL", callId);

    // Upsert agent if it doesn't exist
    const agent = await agentService.upsertAgent({
      customerAgentId: agentId,
      ownerId,
    });

    await transcribeAndSaveCall({
      callId,
      stereoRecordingUrl,
      createdAt: createdAt,
      agentId: agent.id,
      metadata,
      ownerId,
      saveRecording,
      language,
    });

    await sqs.deleteMessage({
      QueueUrl: queueUrl,
      ReceiptHandle: message.ReceiptHandle!,
    });
  } catch (error) {
    console.error("Error processing message:", error, message.Body);
  }
}

export async function startQueueConsumer() {
  const semaphore = new Semaphore(5);
  const queueUrl = env.SQS_QUEUE_URL!;
  const activeProcesses: Promise<void>[] = [];

  while (true) {
    try {
      // Clean up completed processes
      for (let i = activeProcesses.length - 1; i >= 0; i--) {
        const status = await Promise.race([
          activeProcesses[i],
          Promise.resolve("pending"),
        ]);
        if (status !== "pending") {
          activeProcesses.splice(i, 1);
        }
      }

      // Only fetch new messages if we have capacity
      if (activeProcesses.length < 5) {
        const response = await sqs.receiveMessage({
          QueueUrl: queueUrl,
          MaxNumberOfMessages: 5 - activeProcesses.length,
          WaitTimeSeconds: 5,
        });

        if (response.Messages) {
          for (const message of response.Messages) {
            await semaphore.acquire();
            const processPromise = processMessage(message, queueUrl).finally(
              () => {
                semaphore.release();
              },
            );
            activeProcesses.push(processPromise);
          }
        } else {
          // console.log("No messages in queue");
        }
      }
    } catch (error) {
      console.error("Error processing queue:", error);
    }

    // Small delay to prevent tight loop
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}
