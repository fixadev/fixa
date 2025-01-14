import { Textarea } from "~/components/ui/textarea";
import { Label } from "~/components/ui/label";

interface TextAreaWithLabelProps {
  label: string;
  value: string;
  onChange: (value: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
}

export const TextAreaWithLabel = ({
  label,
  value,
  onChange,
  placeholder,
}: TextAreaWithLabelProps) => {
  return (
    <div className="flex flex-col gap-2">
      <Label>{label}</Label>
      <Textarea
        className="min-h-[100px]"
        value={value}
        onChange={(e) => onChange(e)}
        placeholder={placeholder}
      />
    </div>
  );
};
