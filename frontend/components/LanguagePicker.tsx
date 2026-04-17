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
    <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {languages.map((lang) => {
        const meta = LANGUAGE_META[lang] ?? { flag: lang.substring(0,2).toUpperCase(), native: lang };
        const active = selected === lang;
        return (
          <button
            key={lang}
            type="button"
            onClick={() => onSelect(lang)}
            className={`glass card-hover flex items-center gap-5 p-6 text-left transition-all duration-200 overflow-hidden relative cursor-pointer
              ${active ? "border-[4px] border-primary bg-primary/10 shadow-[8px_8px_0px_0px_var(--primary)] translate-x-[-2px] translate-y-[-2px]" : "bg-white"}`
            }
          >
            <div className={`relative flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border-[3px] transition-all font-display text-lg tracking-widest ${active ? 'border-primary text-primary bg-white' : 'border-border text-slate-500 bg-slate-50'}`}>
              {meta.flag}
            </div>
            
            <div className="relative z-10">
              <p className={`font-display text-2xl font-bold tracking-wide uppercase transition-colors ${active ? 'text-primary' : 'text-ink'}`}>{lang}</p>
              <p className="mt-1 font-body text-sm font-bold tracking-widest text-ink/50 uppercase">{meta.native}</p>
            </div>
            
            {active && <span className="absolute top-6 right-6 text-primary font-bold text-xl">✓</span>}
          </button>
        );
      })}
    </div>
  );
}
