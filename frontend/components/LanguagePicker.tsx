const LANGUAGE_META: Record<string, { flag: string; native: string }> = {
  English: { flag: "EN", native: "English" },
  Hindi: { flag: "HI", native: "हिन्दी" },
  Tamil: { flag: "TA", native: "தமிழ்" },
  Telugu: { flag: "TE", native: "తెలుగు" },
  Spanish: { flag: "ES", native: "Español" },
  French: { flag: "FR", native: "Français" },
  Korean: { flag: "KO", native: "한국어" },
};

type Props = {
  languages: string[];
  selected: string;
  onSelect: (lang: string) => void;
};

export function LanguagePicker({ languages, selected, onSelect }: Props) {
  return (
    <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {languages.map((lang) => {
        const meta = LANGUAGE_META[lang] ?? { flag: lang.substring(0,2).toUpperCase(), native: lang };
        const active = selected === lang;
        return (
          <button
            key={lang}
            type="button"
            onClick={() => onSelect(lang)}
            className={`glass card-hover flex items-center gap-5 rounded-[24px] p-6 text-left transition-all duration-500 overflow-hidden relative group
              ${active ? "bg-white/10 border-white/30" : ""}`
            }
          >
            {active && <div className="absolute inset-0 bg-coral/10 blur-xl opacity-50" />}
            
            <div className={`relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full border transition-all duration-500 ${active ? 'border-coral text-coral bg-coral/10' : 'border-white/10 text-white/40 bg-white/5 group-hover:border-white/30 group-hover:text-white/80'}`}>
              <span className="font-display font-medium text-sm tracking-widest">{meta.flag}</span>
            </div>
            
            <div className="relative z-10">
              <p className={`font-display text-2xl font-light tracking-wide transition-colors ${active ? 'text-white' : 'text-white/80 group-hover:text-white'}`}>{lang}</p>
              <p className="mt-1 text-sm font-light tracking-widest text-white/40 uppercase">{meta.native}</p>
            </div>
            
            {active && <span className="absolute top-6 right-6 text-coral text-xs tracking-widest">✓</span>}
          </button>
        );
      })}
    </div>
  );
}
