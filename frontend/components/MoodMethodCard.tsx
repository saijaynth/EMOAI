type Props = {
  title: string;
  subtitle: string;
  icon: string;
  active: boolean;
  ready: boolean;
  onClick: () => void;
};

export function MoodMethodCard({ title, subtitle, icon, active, ready, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!ready}
      className={`glass card-hover p-8 text-left transition-all duration-200 overflow-hidden relative min-h-[200px] flex flex-col justify-between cursor-pointer
        ${active ? "border-[4px] border-secondary bg-secondary/10 shadow-[8px_8px_0px_0px_var(--secondary)] translate-x-[-2px] translate-y-[-2px]" : "bg-white hover:bg-gray-50"}
        ${!ready ? "opacity-50 cursor-not-allowed scale-95 hover:scale-95 shadow-none" : ""}`}
    >
      <div className={`text-5xl transition-transform duration-300 ${active ? "scale-110" : ""}`}>
        {icon}
      </div>

      <div className="relative z-10 mt-6">
        <h3 className={`font-display text-2xl uppercase tracking-wider font-bold transition-colors ${active ? "text-secondary" : "text-ink"}`}>{title}</h3>
        <p className="mt-2 font-body font-bold text-sm leading-relaxed text-ink/60">{subtitle}</p>
      </div>

      {!ready && (
        <span className="absolute top-4 right-4 rounded-md border-2 border-border bg-gray-200 px-3 py-1 font-bold text-xs tracking-widest uppercase text-ink/50">
          Coming Soon
        </span>
      )}
    </button>
  );
}
