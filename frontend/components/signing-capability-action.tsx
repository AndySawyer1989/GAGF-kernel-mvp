import type {
  SigningCapability
} from "@/lib/signing-capability";

type SigningCapabilityActionProps = {
  capability: SigningCapability;
  busy?: boolean;
  loading?: boolean;
  onActivate: () => void;
};

function buttonLabel(
  capability: SigningCapability,
  busy: boolean
): string {
  if (busy) {
    return "Creating signed checkpoint...";
  }

  if (capability.status === "loading") {
    return "Checking signing...";
  }

  return "Create signed checkpoint";
}

export function SigningCapabilityAction({
  capability,
  busy = false,
  loading = false,
  onActivate
}: SigningCapabilityActionProps) {
  const disabled =
    busy ||
    loading ||
    !capability.available;

  return (
    <button
      aria-describedby={
        capability.available
          ? undefined
          : "signed-checkpoint-capability-help"
      }
      className="refresh-button"
      disabled={disabled}
      onClick={onActivate}
      title={
        capability.available
          ? "Create and sign a new audit checkpoint"
          : capability.message
      }
      type="button"
    >
      {buttonLabel(capability, busy)}
    </button>
  );
}
