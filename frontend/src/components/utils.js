export const GENRE_EMOJI = {
  pop: "🎤",
  rock: "🎸",
  "hip-hop": "🎤",
  jazz: "🎷",
  classical: "🎻",
  electronic: "🎧",
  "r&b": "🎙️",
  country: "🤠",
  metal: "🤘",
  indie: "🎸",
  latin: "💃",
  blues: "🎺",
  reggae: "🌴",
  folk: "🪕",
  soul: "❤️‍🔥",
};

export const GRADIENTS = [
  ["#1DB954", "#0e4f25"],
  ["#A29BFE", "#6c5ce7"],
  ["#FF6B6B", "#c0392b"],
  ["#FFEAA7", "#f39c12"],
  ["#4e9af1", "#2980b9"],
  ["#fd79a8", "#e84393"],
  ["#55efc4", "#00b894"],
  ["#fdcb6e", "#e17055"],
  ["#74b9ff", "#0984e3"],
  ["#a29bfe", "#6c5ce7"],
];

export const getGradient = (i) => GRADIENTS[Math.abs(i) % GRADIENTS.length];

export const escapeHtml = (str) => {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
};
