import sys

with open("frontend/components/ResultsScreen.tsx", "r", encoding="utf-8") as f:
    text = f.read()

old_colors = """const MOOD_COLORS: Record<string, string> = {
  happy: "bg-yellow-300 text-yellow-900 border-yellow-400",
  excited: "bg-orange-400 text-orange-950 border-orange-500",
  calm: "bg-green-300 text-green-900 border-green-400",
  focused: "bg-blue-300 text-blue-900 border-blue-400",
  sad: "bg-indigo-300 text-indigo-900 border-indigo-400",
  angry: "bg-red-400 text-red-950 border-red-500",
  anxious: "bg-purple-300 text-purple-900 border-purple-400",
  neutral: "bg-gray-300 text-gray-900 border-gray-400",
};"""

new_colors = """const MOOD_COLORS: Record<string, string> = {
  happy: "bg-yellow-300 text-yellow-900 border-yellow-400",
  excited: "bg-orange-400 text-orange-950 border-orange-500",
  calm: "bg-green-300 text-green-900 border-green-400",
  focused: "bg-blue-300 text-blue-900 border-blue-400",
  sad: "bg-indigo-300 text-indigo-900 border-indigo-400",
  angry: "bg-red-400 text-red-950 border-red-500",
  anxious: "bg-purple-300 text-purple-900 border-purple-400",
  neutral: "bg-gray-300 text-gray-900 border-gray-400",
  romantic: "bg-pink-300 text-pink-900 border-pink-400",
  nostalgic: "bg-amber-200 text-amber-900 border-amber-300",
  confident: "bg-emerald-300 text-emerald-900 border-emerald-400",
  dreamy: "bg-fuchsia-200 text-fuchsia-900 border-fuchsia-300",
  triumphant: "bg-amber-400 text-amber-950 border-amber-500",
  chill: "bg-cyan-200 text-cyan-900 border-cyan-300",
  hype: "bg-rose-400 text-rose-950 border-rose-500",
  melancholic: "bg-slate-400 text-slate-900 border-slate-500",
  hopeful: "bg-teal-300 text-teal-900 border-teal-400",
  frustrated: "bg-stone-400 text-stone-900 border-stone-500",
  bored: "bg-zinc-300 text-zinc-800 border-zinc-400",
};"""

text = text.replace(old_colors, new_colors)

with open("frontend/components/ResultsScreen.tsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Done updating colors.")
