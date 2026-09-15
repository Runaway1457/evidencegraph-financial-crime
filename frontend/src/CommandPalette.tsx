import {
  Bot,
  FileSearch,
  FolderKanban,
  GitBranch,
  Keyboard,
  Search,
  ShieldCheck,
} from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

const commands = [
  { icon: FolderKanban, label: "Open case", hint: "G then C" },
  { icon: GitBranch, label: "Trace selected relationship", hint: "T" },
  { icon: FileSearch, label: "Verify evidence chain", hint: "V" },
  { icon: Bot, label: "Start governed investigation", hint: "⌘ ↵" },
] as const;

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  if (!open) return null;

  return (
    <div className="command-backdrop" onMouseDown={onClose} role="presentation">
      <section
        aria-label="Command palette"
        aria-modal="true"
        className="command-palette"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="command-search">
          <Search aria-hidden="true" size={18} />
          <input
            aria-label="Search commands"
            autoFocus
            placeholder="Search cases, entities, evidence, or commands…"
            type="search"
          />
          <kbd>ESC</kbd>
        </div>
        <div className="command-context">
          <span><ShieldCheck size={13} /> Case-scoped access</span>
          <span>EG-2026-0147</span>
        </div>
        <div className="command-list">
          <small>Investigation actions</small>
          {commands.map(({ icon: Icon, label, hint }) => (
            <button key={label} onClick={onClose} type="button">
              <span><Icon size={17} /> {label}</span>
              <kbd>{hint}</kbd>
            </button>
          ))}
        </div>
        <footer>
          <span><Keyboard size={13} /> Navigate with ↑ ↓</span>
          <span>Enter to run</span>
        </footer>
      </section>
    </div>
  );
}
