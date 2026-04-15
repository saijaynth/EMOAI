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
    <article className="glass card-hover rounded-2xl p-4 flex flex-col gap-3">
      <div>
        <h4 className="font-display text-lg font-semibold leading-tight">{title}</h4>
        <p className="text-sm text-white/70">{artist}</p>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-amber">{language}</span>
        <span className="text-white/20">·</span>
        <div className="flex flex-1 items-center gap-2">
          <div className="h-1.5 flex-1 rounded-full bg-white/15">
            <div className="h-full rounded-full bg-coral" style={{ width: `${energy * 100}%` }} />
          </div>
          <span className="text-xs text-white/40">{Math.round(energy * 100)}%</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {moods.map((mood) => (
          <span key={mood} className="rounded-full bg-white/10 px-2 py-0.5 text-xs capitalize">
            {mood}
          </span>
        ))}
      </div>

      <div className="flex gap-2 pt-1">
        {(["like", "save", "skip"] as const).map((action) => {
          const icons = { like: "❤️", save: "🔖", skip: "⏭️" };
          const active = feedbackState === action;
          return (
            <button
              key={action}
              type="button"
              onClick={() => onFeedback(action)}
              className={`flex-1 rounded-xl py-1.5 text-xs font-semibold transition ${
                active ? "bg-coral text-white" : "bg-white/10 text-white/60 hover:bg-white/20"
              }`}
            >
              {icons[action]} {action}
            </button>
          );
        })}
      </div>

      <a
        href={spotifySearchUrl}
        target="_blank"
        rel="noreferrer"
        className="rounded-xl border border-white/15 px-3 py-2 text-center text-xs font-semibold text-white/80 hover:border-coral hover:text-coral transition"
      >
        Open in Spotify Search
      </a>
    </article>
  );
}
