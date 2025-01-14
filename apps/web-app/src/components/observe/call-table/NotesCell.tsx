import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "~/components/ui/popover";
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import { useState } from "react";
import { type CallWithIncludes } from "@repo/types/src";
import { DocumentTextIcon as DocumentTextIconOutline } from "@heroicons/react/24/outline";
import { DocumentTextIcon as DocumentTextIconSolid } from "@heroicons/react/24/solid";
import { api } from "~/trpc/react";
import { useToast } from "~/components/hooks/use-toast";

export const NotesCell = ({ call }: { call: CallWithIncludes }) => {
  const [isEditing, setIsEditing] = useState(
    !(call?.notes?.length && call?.notes?.length > 0),
  );
  const [notes, setNotes] = useState(call?.notes ?? "");
  const { toast } = useToast();

  const { mutate: updateCall } = api._call.updateNotes.useMutation({
    onSuccess: () => {
      toast({
        title: "notes updated successfully",
      });
    },
    onError: () => {
      toast({
        title: "failed to update notes",
        variant: "destructive",
      });
    },
  });

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    console.log("saving notes", notes, "for call", call.id);
    updateCall({
      callId: call.id,
      notes,
    });
    setIsEditing(false);
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          className="h-auto items-center justify-center p-0 pt-1 text-xs text-muted-foreground hover:bg-transparent"
          onClick={(e) => e.stopPropagation()}
        >
          {notes.length && notes.length > 0 ? (
            <DocumentTextIconSolid className="size-5 text-gray-700" />
          ) : (
            <DocumentTextIconOutline className="size-5" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" onClick={(e) => e.stopPropagation()}>
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="min-h-[100px]"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(false);
                }}
              >
                cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                save
              </Button>
            </div>
          </div>
        ) : (
          <div
            className="cursor-pointer whitespace-pre-wrap p-2 text-sm hover:bg-muted"
            onClick={(e) => {
              e.stopPropagation();
              setIsEditing(true);
            }}
          >
            {notes || "click to add notes..."}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
};
