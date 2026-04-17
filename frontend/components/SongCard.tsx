type Props = {
  title: string;
  artist: string;
  language: string;
  moods: string[];
  energy: number;
  feedbackState?: string;
  onFeedback: (action: "like" | "skip" | "save") => void;
  spotifySearchUrl: string;
};

export function SongCard({ title, artist, language, moods, energy, feedbackState, onFeedback, spotifySearchUrl }: Props) {
  return (
    <article className="glass card-hover bg-white p-5 flex flex-col gap-4">
      <div>
        <h4 className="font-display text-xl font-bold tracking-wide text-ink leading-tight">{title}</h4>
        <p className="text-sm font-medium text-ink/70">{artist}</p>
      </div>

      <div className="flex items-center gap-3">
        <span className="font-display text-xs uppercase tracking-wider text-primary border-2 border-primary/20 px-2 py-0.5 rounded-md bg-primary/5">{language}</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {moods.map((mood) => (
          <span key={mood} className="border-2 border-border bg-slate-50 px-2.5 py-1 text-xs font-bold uppercase tracking-wider rounded-md">
            {mood}
          </span>
        ))}
      </div>

      <div className="flex gap-3 pt-2">
        {(["like", "save", "skip"] as const).map((action) => {
          const icons = { like: "❤️", save: "🔖", skip: "⏭️" };
          const active = feedbackState === action;
          return (
            <button
              key={action}
              type="button"
              onClick={() => onFeedback(action)}
              className={`flex-1 border-[3px] border-border rounded-lg py-2 text-sm font-bold transition transform active:translate-y-1 cursor-pointer ${
                active ? "bg-secondary text-white shadow-[0px_0px_0px_0px_var(--border-color)] translate-y-1" : "bg-white text-ink hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_var(--border-color)]"
              }`}
            >
              {icons[action]} <span className="uppercase ml-1">{action}</span>
            </button>
          );
        })}
      </div>

      <a
        href={spotifySearchUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-2 block w-full border-[3px] border-border bg-green-400 text-white rounded-lg py-2.5 text-center text-sm font-bold uppercase tracking-wide hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_var(--border-color)] transition active:translate-y-1 active:shadow-none cursor-pointer"
      >
        Open in Spotify
      </a>
    </article>
  );
}
