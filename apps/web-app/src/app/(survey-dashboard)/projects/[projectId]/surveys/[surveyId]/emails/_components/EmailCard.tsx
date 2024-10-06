import { CheckCircleIcon } from "@heroicons/react/24/solid";
import { formatDistanceToNow } from "date-fns";
import { type Email } from "prisma/generated/zod";
import { Avatar, AvatarFallback } from "~/components/ui/avatar";
import { cn } from "~/lib/utils";

export default function EmailCard({
  email,
  subject = "123 Main St",
  draft = false,
  unread = false,
  completed = false,
  warning = "",
  expanded = false,
  onClick,
  className,
}: {
  email: Email;
  subject?: string;
  draft?: boolean;
  unread?: boolean;
  completed?: boolean;
  warning?: string;
  expanded?: boolean;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-md border border-input shadow-sm",
        completed ? "opacity-50" : "",
        className,
      )}
    >
      <div
        className="flex cursor-pointer items-start gap-2 rounded-md p-4 hover:bg-muted"
        onClick={(e) => {
          onClick?.(e);
        }}
      >
        <div
          className={cn([
            "-my-4 -ml-4 w-1.5 self-stretch rounded-l-md bg-blue-500 py-4",
            unread ? "visible" : "invisible",
          ])}
        ></div>
        {!draft && (
          <Avatar className="mt-1">
            <AvatarFallback>
              {email.senderName
                .split(" ")
                .map((name) => name[0])
                .join("")}
            </AvatarFallback>
          </Avatar>
        )}
        <div className="flex-1 space-y-1 overflow-hidden">
          <div className="flex items-center justify-between">
            {draft ? (
              <div className="text-sm">
                <span className="text-destructive">[Draft]</span>{" "}
                {email.senderEmail}
              </div>
            ) : (
              <div className={cn("text-base", unread ? "font-medium" : "")}>
                {email.senderName}
              </div>
            )}
            {!draft &&
              (completed ? (
                <CheckCircleIcon className="size-5 text-green-500" />
              ) : warning ? (
                <div className="rounded-full bg-orange-100 px-2 py-1 text-xs">
                  {warning}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(email.createdAt), {
                    addSuffix: true,
                  })}
                </div>
              ))}
          </div>
          <div className={cn("text-sm", unread ? "font-medium" : "")}>
            {subject}
          </div>
          {!expanded && (
            <div
              className={cn(
                "overflow-hidden truncate text-sm text-muted-foreground",
                draft ? "italic" : "",
              )}
            >
              {email.body}
            </div>
          )}
        </div>
      </div>
      {expanded && (
        <div className="p-4 pl-6">
          {email.body.split("\n").map((line, index) => (
            <p key={index} className="min-h-5 text-sm">
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}