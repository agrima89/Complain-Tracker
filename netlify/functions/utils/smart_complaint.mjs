/**
 * CampusCare - Smart Complaint & Resolution Intelligence Module
 * Provides lightweight heuristic analysis for:
 * 1. Smart Complaint Detection (Category, Priority, Location, Reason)
 * 2. Similar / Duplicate Complaint Detection (Keyword TF-IDF / Jaccard similarity)
 */

export const VALID_CATEGORIES = [
  "Electrical", "Cleaning", "Hostel", "Wi-Fi/Internet", "Classroom",
  "Library", "Infrastructure", "Transport Complaint", "Other"
];

export const VALID_BLOCKS = [
  "Block A", "Block B", "Block C", "Block D", "Block E", "Block F",
  "Academic Block", "Hostel", "Library", "Campus", "Sports", "Other"
];

export const CATEGORY_KEYWORDS = {
  "Electrical": {
    "spark": 4, "sparking": 4, "shock": 5, "short circuit": 5, "wire": 3, "wiring": 3,
    "power": 2, "electricity": 3, "blackout": 4, "light": 2, "bulb": 2, "tube": 2,
    "tubelight": 3, "fan": 2, "ac": 2, "air conditioner": 3, "heater": 2, "geyser": 3,
    "socket": 3, "switch": 2, "switchboard": 3, "mcb": 4, "breaker": 3, "plug": 2,
    "generator": 3, "voltage": 3, "fluctuation": 3, "dark": 2, "fuse": 3, "tripped": 3
  },
  "Cleaning": {
    "water": 2, "leak": 3, "leakage": 4, "leaking": 4, "pipe": 3, "tap": 3, "faucet": 3,
    "sink": 3, "washroom": 3, "toilet": 4, "restroom": 3, "flush": 3, "dirty": 3,
    "clean": 2, "cleaning": 3, "garbage": 3, "trash": 3, "dustbin": 2, "waste": 2,
    "smell": 3, "stench": 3, "odor": 3, "foul": 3, "cockroach": 3, "insect": 2,
    "pest": 3, "mosquito": 2, "mop": 2, "slippery": 4, "puddle": 3, "overflow": 4,
    "stain": 2, "dust": 2, "sanitation": 3, "drain": 4, "drainage": 4, "choked": 4,
    "clogged": 4, "blocked": 3
  },
  "Hostel": {
    "hostel": 5, "room": 2, "warden": 4, "mess": 4, "food": 3, "bed": 3, "mattress": 3,
    "cupboard": 3, "almirah": 3, "roommate": 3, "curfew": 3, "balcony": 2, "cooler": 2,
    "laundry": 3, "washing machine": 3, "water cooler": 3, "canteen": 2, "wing": 2,
    "corridor": 2, "iron": 2, "hot water": 3, "hostel gate": 3, "guards": 2, "curtain": 2
  },
  "Wi-Fi/Internet": {
    "wifi": 5, "wi-fi": 5, "internet": 5, "network": 4, "lan": 4, "ethernet": 4,
    "router": 4, "speed": 3, "slow": 3, "offline": 4, "disconnect": 4, "disconnected": 4,
    "portal": 3, "login": 2, "signal": 3, "bandwidth": 3, "connection": 3, "connecting": 3,
    "ping": 2, "dns": 3, "server down": 4, "cable": 2
  },
  "Classroom": {
    "projector": 5, "screen": 3, "podium": 3, "mic": 4, "microphone": 4, "speaker": 3,
    "sound": 2, "audio": 2, "bench": 3, "desk": 3, "chair": 2, "board": 3, "whiteboard": 3,
    "blackboard": 3, "marker": 2, "duster": 2, "classroom": 4, "lecture": 3, "hall": 2,
    "smart board": 4, "hdmi": 3, "display": 2
  },
  "Library": {
    "book": 4, "books": 4, "library": 5, "librarian": 4, "issue": 3, "return": 3,
    "barcode": 3, "reading room": 4, "reference": 3, "journal": 3, "magazine": 2,
    "study hall": 4, "quiet": 2, "noise": 3, "digital library": 4, "catalog": 3, "fine": 2
  },
  "Infrastructure": {
    "door": 3, "window": 3, "glass": 4, "broken glass": 5, "lock": 3, "handle": 2,
    "wall": 3, "ceiling": 3, "roof": 3, "tiles": 3, "plaster": 3, "crack": 4,
    "paint": 2, "lift": 4, "elevator": 4, "stuck lift": 5, "stairs": 3, "staircase": 3,
    "railing": 4, "road": 3, "pothole": 4, "parking": 3, "gate": 3, "boundary": 2,
    "furniture": 3, "table": 2, "structural": 4, "collapse": 5, "damage": 3
  }
};

export const PRIORITY_URGENT_KEYWORDS = {
  "emergency": 6, "dangerous": 5, "danger": 5, "shock": 6, "electric shock": 7,
  "spark": 5, "sparking": 6, "fire": 7, "smoke": 6, "burning": 6, "short circuit": 6,
  "flood": 5, "flooding": 5, "slippery": 4, "broken glass": 5, "lift stuck": 6,
  "trapped": 6, "hazard": 5, "hazardous": 5, "unsafe": 5, "injury": 6, "hurt": 5,
  "accident": 5, "urgent": 4, "urgently": 4, "immediate": 4, "collapse": 6, "falling": 5,
  "choked drain": 4, "blackout": 4, "gas leak": 7, "snake": 6, "medical": 5
};

export const PRIORITY_MEDIUM_KEYWORDS = {
  "broken": 3, "not working": 3, "malfunction": 3, "stopped": 3, "leak": 3, "leakage": 3,
  "slow": 2, "damaged": 3, "faulty": 3, "smell": 2, "dirty": 2, "choked": 3, "clogged": 3,
  "noise": 2, "flickering": 2, "offline": 2, "error": 2, "issue": 1, "problem": 1
};

export const PRIORITY_LOW_KEYWORDS = {
  "minor": 3, "request": 3, "suggestion": 3, "replace": 2, "dust": 2, "cosmetic": 3,
  "paint": 2, "update": 2, "inquiry": 3, "query": 3, "routine": 2, "slowly": 1
};

export const LOCATION_KEYWORD_MAP = [
  [/\bgirls?\s*hostel\b|\bgh\b|\bgirls?\s*wing\b/i, "Hostel", "Girls Hostel"],
  [/\bboys?\s*hostel\b|\bbh\b|\bboys?\s*wing\b/i, "Hostel", "Boys Hostel"],
  [/\bhostel\b|\bmess\b|\bwarden\b/i, "Hostel", "Hostel"],
  [/\blibrary\b|\breading\s*room\b/i, "Library", "Central Library"],
  [/\bsports?\b|\bgym\b|\bground\b|\bcourt\b|\bstadium\b/i, "Sports", "Sports Complex"],
  [/\bacademic\s*block\b|\bacademic\b/i, "Academic Block", "Academic Block"],
  [/\bblock\s*a\b|\bblock-a\b|\bsector\s*a\b/i, "Block A", "Block A"],
  [/\bblock\s*b\b|\bblock-b\b|\bsector\s*b\b/i, "Block B", "Block B"],
  [/\bblock\s*c\b|\bblock-c\b|\bsector\s*c\b/i, "Block C", "Block C"],
  [/\bblock\s*d\b|\bblock-d\b|\bsector\s*d\b/i, "Block D", "Block D"],
  [/\bblock\s*e\b|\bblock-e\b|\bsector\s*e\b/i, "Block E", "Block E"],
  [/\bblock\s*f\b|\bblock-f\b|\bsector\s*f\b/i, "Block F", "Block F"],
  [/\bcafeteria\b|\bcanteen\b|\bfood\s*court\b/i, "Campus", "Cafeteria / Food Court"],
  [/\bparking\b|\bvehicle\b|\bbike\s*stand\b/i, "Campus", "Parking Area"],
  [/\blab\b|\blaboratory\b|\bcomputer\s*lab\b/i, "Academic Block", "Computer / Science Labs"],
  [/\bauditorium\b|\baudi\b|\bseminar\s*hall\b/i, "Campus", "Auditorium / Seminar Hall"],
  [/\bwashroom\b|\btoilet\b|\brestroom\b/i, "Academic Block", "Restroom / Washroom Area"]
];

export const STOP_WORDS = new Set([
  "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
  "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
  "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
  "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
  "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
  "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
  "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
  "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
  "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
  "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
  "why", "with", "you", "your", "yours", "yourself", "yourselves", "please", "kindly", "sir", "madam"
]);

export function tokenizeText(text) {
  if (!text) return [];
  const cleaned = text.toLowerCase().replace(/[^\w\s-]/g, " ");
  return cleaned.split(/\s+/).map(w => w.trim()).filter(w => w.length > 1);
}

export function detectCategory(text) {
  const textLower = text.toLowerCase();
  const scores = {};
  const matchedWords = {};
  for (const cat of VALID_CATEGORIES) {
    scores[cat] = 0;
    matchedWords[cat] = [];
  }

  for (const [cat, kwDict] of Object.entries(CATEGORY_KEYWORDS)) {
    if (!(cat in scores)) continue;
    for (const [kw, weight] of Object.entries(kwDict)) {
      if (kw.includes(" ")) {
        if (textLower.includes(kw)) {
          scores[cat] += weight * 2;
          matchedWords[cat].push(kw);
        }
      } else {
        const regex = new RegExp(`\\b${kw}\\b`, "g");
        const matches = (textLower.match(regex) || []).length;
        if (matches > 0) {
          scores[cat] += weight * matches;
          matchedWords[cat].push(kw);
        }
      }
    }
  }

  let bestCat = "Other";
  let maxScore = 0;
  for (const [cat, score] of Object.entries(scores)) {
    if (score > maxScore) {
      maxScore = score;
      bestCat = cat;
    }
  }

  if (maxScore === 0) {
    bestCat = "Infrastructure";
  }

  return {
    category: bestCat,
    score: maxScore,
    matchedKeywords: matchedWords[bestCat] || []
  };
}

export function detectPriority(text, category = "Other") {
  const textLower = text.toLowerCase();
  let highScore = 0;
  let medScore = 0;
  let lowScore = 0;
  const urgencyReasons = [];

  for (const [kw, weight] of Object.entries(PRIORITY_URGENT_KEYWORDS)) {
    if (kw.includes(" ")) {
      if (textLower.includes(kw)) {
        highScore += weight * 2;
        urgencyReasons.push(kw);
      }
    } else {
      if (new RegExp(`\\b${kw}\\b`, "i").test(textLower)) {
        highScore += weight;
        urgencyReasons.push(kw);
      }
    }
  }

  for (const [kw, weight] of Object.entries(PRIORITY_MEDIUM_KEYWORDS)) {
    if (kw.includes(" ")) {
      if (textLower.includes(kw)) medScore += weight;
    } else {
      if (new RegExp(`\\b${kw}\\b`, "i").test(textLower)) medScore += weight;
    }
  }

  for (const [kw, weight] of Object.entries(PRIORITY_LOW_KEYWORDS)) {
    if (new RegExp(`\\b${kw}\\b`, "i").test(textLower)) lowScore += weight;
  }

  let priority = "Medium";
  if (highScore >= 4 || (highScore > 0 && (category === "Electrical" || category === "Cleaning"))) {
    priority = "High";
  } else if (medScore >= 2 || highScore > 0) {
    priority = "Medium";
  } else if (lowScore > medScore && lowScore > 0) {
    priority = "Low";
  }

  return { priority, urgencyReasons };
}

export function detectLocation(text) {
  const textLower = text.toLowerCase();
  for (const [pattern, block, label] of LOCATION_KEYWORD_MAP) {
    if (pattern.test(textLower)) {
      return { block, specificLabel: label };
    }
  }

  const roomMatch = textLower.match(/\b([a-f])[- ]?([1-9][0-9]{2})\b/i);
  if (roomMatch) {
    const blockLetter = roomMatch[1].toUpperCase();
    const blockName = `Block ${blockLetter}`;
    if (VALID_BLOCKS.includes(blockName)) {
      return { block: blockName, specificLabel: `${blockName}, Room ${roomMatch[2]}` };
    }
  }

  return { block: "", specificLabel: "" };
}

export function generateReason(category, priority, locationLabel, matchedKeywords, urgencyReasons) {
  const parts = [];
  if (urgencyReasons.length > 0) {
    parts.push(`${urgencyReasons.slice(0, 2).join(', ')} safety factor detected`);
  } else if (matchedKeywords.length > 0) {
    parts.push(`${matchedKeywords.slice(0, 2).join(', ')} domain detected`);
  }

  if (locationLabel) {
    parts.push(`located at ${locationLabel}`);
  }

  if (priority === "High" && !parts.some(p => p.includes("safety"))) {
    parts.push("elevated urgency assigned");
  }

  if (parts.length === 0) {
    return "Automatic contextual campus analysis";
  }

  const capitalized = parts.join(" + ");
  return capitalized.charAt(0).toUpperCase() + capitalized.slice(1);
}

export function analyzeComplaint(text) {
  if (!text || text.trim().length < 5) {
    return { success: false, message: "Text too short for analysis" };
  }

  const { category, score: catScore, matchedKeywords } = detectCategory(text);
  const { priority, urgencyReasons } = detectPriority(text, category);
  const { block, specificLabel: locationLabel } = detectLocation(text);
  const reason = generateReason(category, priority, locationLabel, matchedKeywords, urgencyReasons);

  const confidence = Math.min(0.95, Number((0.45 + (catScore * 0.05) + (urgencyReasons.length * 0.1)).toFixed(2)));

  return {
    success: true,
    category,
    priority,
    location: block || locationLabel || "Campus",
    block,
    location_block: block,
    location_label: locationLabel || block || "Campus Premises",
    reason,
    confidence,
    keywords: [...matchedKeywords, ...urgencyReasons]
  };
}

export function getCleanKeywords(text) {
  const tokens = tokenizeText(text);
  return new Set(tokens.filter(w => !STOP_WORDS.has(w) && w.length > 2));
}

export function computeSimilarityScore(desc1, desc2, cat1 = null, cat2 = null, block1 = null, block2 = null) {
  const kw1 = getCleanKeywords(desc1);
  const kw2 = getCleanKeywords(desc2);

  if (kw1.size === 0 || kw2.size === 0) return 0.0;

  const intersection = new Set([...kw1].filter(x => kw2.has(x)));
  const union = new Set([...kw1, ...kw2]);
  const jaccard = union.size > 0 ? intersection.size / union.size : 0.0;

  let bonus = 0.0;
  for (const kw of intersection) {
    if (kw.length >= 5) bonus += 0.05;
  }
  bonus = Math.min(0.15, bonus);
  const tokenScore = Math.min(1.0, jaccard + bonus);

  let catMatchScore = 0.0;
  if (cat1 && cat2 && cat1 === cat2) catMatchScore = 1.0;

  let blockMatchScore = 0.0;
  if (block1 && block2 && block1.toLowerCase() === block2.toLowerCase() && !["", "other", "campus"].includes(block1.toLowerCase())) {
    blockMatchScore = 1.0;
  }

  const totalScore = (tokenScore * 0.60) + (catMatchScore * 0.20) + (blockMatchScore * 0.20);
  return Number(totalScore.toFixed(3));
}
