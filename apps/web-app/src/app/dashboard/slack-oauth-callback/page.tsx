"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef } from "react";
import Spinner from "~/components/Spinner";
import { api } from "~/trpc/react";

interface SlackOAuthSearchParams {
  code: string;
  state: string;
}

export default function SlackOAuthCallback({
  searchParams: { code, state },
}: {
  searchParams: SlackOAuthSearchParams;
}) {
  const router = useRouter();
  const { mutateAsync: exchangeCode } = api.slack.exchangeCode.useMutation();
  const { mutateAsync: sendMessage } = api.slack.sendMessage.useMutation();

  const parsedState = useMemo(() => {
    if (!state) {
      return null;
    }
    const parsedState = JSON.parse(state) as {
      agentId: string;
      origin: "dashboard" | "observe";
      savedSearchId?: string;
    };
    return parsedState;
  }, [state]);

  const isExchangingCode = useRef(false);
  useEffect(() => {
    const exchangeCodeAsync = async () => {
      if (code && !isExchangingCode.current) {
        isExchangingCode.current = true;
        try {
          console.log("exchanging code", code);
          await exchangeCode({ code });
          console.log("exchanged code", code);
          console.log("sending message");
          await sendMessage({ message: { text: "hello from fixa :3" } });
          console.log("sent message");
        } catch (error) {
          console.error("Error exchanging code:", error);
        } finally {
          isExchangingCode.current = false;
        }
      }
      console.log("parsedState", parsedState);
      router.push(
        `/${
          parsedState?.origin === "dashboard"
            ? `dashboard/${parsedState.agentId}/slack-app`
            : `observe/${parsedState?.savedSearchId ? "saved/" + parsedState.savedSearchId : "slack-app"}`
        }`,
      );
    };
    void exchangeCodeAsync();
  }, [exchangeCode, code, parsedState, router, sendMessage]);

  return (
    <div className="flex size-full items-center justify-center">
      <div className="flex items-center gap-2">
        <Spinner />
        <div className="text-lg font-medium">adding fixa bot to slack...</div>
      </div>
    </div>
  );
}
