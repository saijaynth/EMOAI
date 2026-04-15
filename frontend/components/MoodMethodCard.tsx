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
      className={`glass card-hover rounded-[24px] p-8 text-left transition-all duration-500 overflow-hidden relative group min-h-[160px] flex flex-col justify-end
        ${active ? "bg-white/10 border-white/30" : ""}
        ${!ready ? "opacity-30 cursor-not-allowed scale-95 hover:scale-95" : "hover:bg-white-[0.03]"}`}
    >
      {active && <div className="absolute inset-0 bg-coral/10 blur-xl opacity-60" />}
      
      <div className={`absolute top-6 right-6 transition-all duration-500 text-4xl filter ${active ? "opacity-100 grayscale-0" : "opacity-30 grayscale group-hover:opacity-50"}`}>
        {icon}
      </div>

      <div className="relative z-10 mt-auto">
        <h3 className={`font-display text-3xl font-light tracking-wide transition-colors duration-500 ${active ? "text-white title-glow" : "text-white/70 group-hover:text-white"}`}>{title}</h3>
        <p className="mt-3 text-sm font-light leading-relaxed text-white/50">{subtitle}</p>
      </div>

      {!ready && (
        <span className="absolute top-6 left-6 rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs tracking-widest uppercase text-white/40 backdrop-blur-md">
          Phase 2
        </span>
      )}
    </button>
  );
}
