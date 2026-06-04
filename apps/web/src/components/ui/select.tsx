"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

type SelectContextValue = {
  disabled?: boolean;
  open: boolean;
  setOpen: (open: boolean) => void;
  value: string;
  setValue: (value: string) => void;
  selectedLabel: ReactNode;
  setItemLabel: (value: string, label: ReactNode) => void;
};

const SelectContext = createContext<SelectContextValue | null>(null);

function useSelect() {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error("Select components must be used inside Select");
  }
  return context;
}

function Select({
  value,
  onValueChange,
  disabled,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [labels, setLabels] = useState<Record<string, ReactNode>>({});

  const context = useMemo<SelectContextValue>(
    () => ({
      disabled,
      open,
      setOpen,
      value,
      setValue: (nextValue) => {
        onValueChange(nextValue);
        setOpen(false);
      },
      selectedLabel: labels[value] ?? value,
      setItemLabel: (itemValue, label) => {
        setLabels((current) => {
          if (current[itemValue] === label) return current;
          return { ...current, [itemValue]: label };
        });
      },
    }),
    [disabled, labels, onValueChange, open, value],
  );

  return (
    <SelectContext.Provider value={context}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
}

function SelectTrigger({
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { disabled, open, setOpen } = useSelect();

  return (
    <button
      type="button"
      aria-expanded={open}
      aria-haspopup="listbox"
      disabled={disabled}
      className={cn(
        "flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      onClick={() => setOpen(!open)}
      {...props}
    >
      <span className="truncate">{children}</span>
      <span aria-hidden className="ml-2 text-xs text-muted-foreground">
        v
      </span>
    </button>
  );
}

function SelectValue() {
  const { selectedLabel } = useSelect();
  return <>{selectedLabel}</>;
}

function SelectContent({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  const { open } = useSelect();
  if (!open) return null;

  return (
    <div
      role="listbox"
      className={cn(
        "absolute z-50 mt-1 max-h-72 w-full overflow-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

function SelectItem({
  value,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  value: string;
}) {
  const { setItemLabel, setValue, value: selectedValue } = useSelect();

  useEffect(() => {
    setItemLabel(value, children);
  }, [children, setItemLabel, value]);

  return (
    <button
      type="button"
      role="option"
      aria-selected={selectedValue === value}
      className={cn(
        "flex w-full items-center rounded-sm px-2 py-1.5 text-left text-sm outline-none hover:bg-muted focus:bg-muted aria-selected:bg-muted",
        className,
      )}
      onClick={() => setValue(value)}
      {...props}
    >
      {children}
    </button>
  );
}

export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue };
