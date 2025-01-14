import {
  CheckCircleIcon,
  CodeBracketIcon,
  WrenchIcon,
  XCircleIcon,
} from "@heroicons/react/24/solid";
import { CallResult, CallStatus } from "@prisma/client";
import { formatDistanceToNow } from "date-fns";
import { useMemo } from "react";
import { ibmPlexMono } from "~/app/fonts";
import { type TestWithCalls } from "@repo/types/src/index";
import { cn, didCallSucceed } from "~/lib/utils";
import Spinner from "../Spinner";

export default function TestCard({
  test,
  className,
}: {
  test: TestWithCalls;
  className?: string;
}) {
  const callsSucceeded = useMemo(
    () => test?.calls?.filter((call) => didCallSucceed(call)) ?? [],
    [test?.calls],
  );

  const callsFailed = useMemo(
    () => test.calls.filter((call) => call.result === CallResult.failure),
    [test.calls],
  );

  const callsInProgress = useMemo(
    () =>
      test.calls.filter((call) => {
        const inProgress =
          call.status === CallStatus.in_progress ||
          call.status === CallStatus.analyzing ||
          call.status === CallStatus.queued;
        const olderThan1Hour =
          call.createdAt &&
          new Date(call.createdAt).getTime() < Date.now() - 1 * 60 * 60 * 1000;

        return inProgress && !olderThan1Hour;
      }),
    [test.calls],
  );

  const callsCompleted = useMemo(
    () => test.calls.filter((call) => call.status === CallStatus.completed),
    [test.calls],
  );

  return (
    <div
      className={cn(
        "flex items-center justify-between border-b border-input p-4",
        className,
      )}
    >
      <div className="flex w-60 items-center gap-3">
        {callsInProgress.length > 0 ? (
          <Spinner className="size-6 shrink-0 text-muted-foreground" />
        ) : callsFailed.length > 0 ? (
          <XCircleIcon className="-mx-0.5 size-7 shrink-0 text-red-500" />
        ) : (
          <CheckCircleIcon className="-mx-0.5 size-7 shrink-0 text-green-500" />
        )}
        <div className="flex flex-col gap-1">
          <div className="font-medium">
            {callsInProgress.length > 0
              ? `${callsCompleted.length}/${test.calls.length} calls completed`
              : `${callsSucceeded.length}/${test.calls.length} checks passed`}
          </div>
          {callsInProgress.length === 0 && callsFailed.length > 0 && (
            <div className="flex h-1.5 w-48 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-green-500 transition-all"
                style={{
                  width: `${(callsSucceeded.length / test.calls.length) * 100}%`,
                }}
              />
              <div
                className="h-full bg-red-500 transition-all"
                style={{
                  width: `${(callsFailed.length / test.calls.length) * 100}%`,
                }}
              />
            </div>
          )}
        </div>
      </div>
      {test.gitBranch && test.gitCommit ? (
        <div className="flex w-60 flex-col gap-2">
          <div className="flex items-center gap-2">
            <div className={cn("text-sm font-medium", ibmPlexMono.className)}>
              {test.gitBranch}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={cn("text-sm font-medium", ibmPlexMono.className)}>
              {test.gitCommit}
            </div>
          </div>
        </div>
      ) : test.runFromApi ? (
        <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <CodeBracketIcon className="size-4" /> run via API
        </div>
      ) : (
        <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <WrenchIcon className="size-4" /> manual run
        </div>
      )}
      <div className="flex gap-2">
        <div className="w-40 text-right text-sm text-muted-foreground">
          {formatDistanceToNow(test.createdAt, { addSuffix: true })}
        </div>
      </div>
    </div>
  );
}
