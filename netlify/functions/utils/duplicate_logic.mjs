/**
 * CampusCare - Complaint Fingerprinting & Duplicate Detection Logic
 * Matches the deterministic fingerprinting and normalization rules of database.py
 */

export const ACTIVE_COMPLAINT_STATUSES = ["NEW", "PENDING", "IN_PROGRESS", "REOPENED", "FORWARDED"];

export function formatTicketId(complaintId, dateStr = null) {
  let year = new Date().getFullYear();
  if (dateStr && typeof dateStr === 'string' && dateStr.length >= 4) {
    const parsedYear = parseInt(dateStr.slice(0, 4), 10);
    if (!isNaN(parsedYear) && parsedYear > 2000) {
      year = parsedYear;
    }
  }
  const paddedId = String(complaintId).padStart(4, '0');
  return `CMP-${year}-${paddedId}`;
}

export function extractCanonicalRoom(roomStr) {
  if (!roomStr) return "";
  const str = String(roomStr);
  const match = str.match(/\b(?:room|rm)?[ -]?(?:[a-z]-?)?([0-9]{2,4}[a-z]?)\b/i);
  if (match) {
    return match[1].toLowerCase();
  }
  return str.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function normalizeIssueText(text, roomNo = "") {
  if (!text) return "";
  let cleanText = String(text).toLowerCase().trim();

  const contractions = {
    "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "weren't": "were not", "don't": "do not", "doesn't": "does not",
    "didn't": "did not", "can't": "can not", "won't": "will not",
    "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "it's": "it is", "that's": "that is"
  };

  for (const [c, expanded] of Object.entries(contractions)) {
    cleanText = cleanText.split(c).join(expanded);
  }

  const words = cleanText.match(/[a-z0-9]+/g) || [];
  const roomDigits = new Set((String(roomNo).match(/[0-9]+/g) || []));

  const stopWords = new Set([
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
    "and", "or", "in", "on", "at", "to", "for", "of", "with", "my", "our",
    "your", "this", "that", "these", "those", "it", "its", "there", "has",
    "have", "had", "do", "does", "did", "please", "kindly", "sir", "madam",
    "help", "issue", "problem", "complaint", "facing", "got", "get", "very",
    "really", "urgently", "urgent", "also", "just", "from", "by", "again",
    "room", "rooms", "ceiling", "properly", "all", "completely", "entirely",
    "totally", "well", "badly", "now", "still", "side", "area", "hall", "lab"
  ]);

  const stemMap = {
    "working": "work", "works": "work", "worked": "work",
    "leaking": "leak", "leaks": "leak", "leaked": "leak", "leakage": "leak",
    "flickering": "flicker", "flickers": "flicker", "flickered": "flicker",
    "sparking": "spark", "sparks": "spark", "sparked": "spark",
    "broken": "break", "breaking": "break", "breaks": "break",
    "choked": "choke", "choking": "choke", "chokes": "choke",
    "clogged": "clog", "clogging": "clog", "clogs": "clog",
    "dripping": "drip", "drips": "drip", "dripped": "drip",
    "fans": "fan", "lights": "light", "lighting": "light", "tubelights": "tubelight",
    "switches": "switch", "switchboards": "switchboard", "sockets": "socket",
    "taps": "tap", "sinks": "sink", "pipes": "pipe", "doors": "door",
    "windows": "window", "chairs": "chair", "benches": "bench",
    "tables": "table", "desks": "desk", "projectors": "projector",
    "routers": "router", "smelling": "smell", "smells": "smell", "ac": "ac",
    "airconditioner": "ac", "airconditioners": "ac",
    "cleaned": "clean", "cleaning": "clean", "cleans": "clean"
  };

  const cleanedTokens = [];
  for (const w of words) {
    if (roomDigits.has(w)) continue;
    if (!stopWords.has(w) && w.length > 1) {
      cleanedTokens.push(stemMap[w] || w);
    }
  }

  return Array.from(new Set(cleanedTokens)).sort().join(" ");
}

export function getCanonicalLocationKey(params = {}) {
  const {
    category = "",
    block = "",
    floor_no = "",
    room_no = "",
    location = "",
    bus_number = "",
    route = "",
    transport_type = ""
  } = params;

  const catNorm = (category || "").trim().toLowerCase();
  if (catNorm === "transport complaint") {
    const normBus = (bus_number || "").replace(/\b(?:bus|no|#|\s)+\b/gi, "").trim().toLowerCase();
    const normRoute = (route || "").trim().toLowerCase().replace(/\s+/g, " ");
    const normType = (transport_type || "").trim().toLowerCase();
    return `transport::${normType}::${normBus}::${normRoute}`;
  }

  let b = (block || location || "").trim().toLowerCase();
  b = b.replace(/[\-_]+/g, " ").replace(/\s+/g, " ");
  const blockMatch = b.match(/\bblock\s*([a-z0-9]+)\b|\b([a-z0-9]+)\s*block\b/i);
  let normBlock = b;
  if (blockMatch) {
    const letter = blockMatch[1] || blockMatch[2];
    normBlock = `block ${letter.toLowerCase()}`;
  }

  const normRoom = extractCanonicalRoom(room_no || location);
  return `${normBlock}::${normRoom}`;
}

export function normalizeLocationKey(params = {}) {
  const {
    category = "",
    block = "",
    floor_no = "",
    room_no = "",
    location = "",
    transport_type = "",
    bus_number = "",
    route = ""
  } = params;

  const catNorm = (category || "").trim().toLowerCase();
  if (catNorm === "transport complaint") {
    const normBus = (bus_number || "").replace(/\b(?:bus|no|#|\s)+\b/gi, "").trim().toLowerCase();
    const normRoute = (route || "").trim().toLowerCase().replace(/\s+/g, " ");
    const normType = (transport_type || "").trim().toLowerCase();
    return `transport:${normType}:${normBus}:${normRoute}`;
  }

  let b = (block || location || "").trim().toLowerCase();
  b = b.replace(/[\-_]+/g, " ").replace(/\s+/g, " ");
  const blockMatch = b.match(/\bblock\s*([a-z0-9]+)\b|\b([a-z0-9]+)\s*block\b/i);
  let normBlock = b;
  if (blockMatch) {
    const letter = blockMatch[1] || blockMatch[2];
    normBlock = `block ${letter.toLowerCase()}`;
  }

  const normRoom = extractCanonicalRoom(room_no || location);
  let f = (floor_no || "").trim().toLowerCase();
  f = f.replace(/\b(?:floor|flr|fl)\b/gi, "").replace(/^[ \-_,.#]+|[ \-_,.#]+$/g, "");

  return `${normBlock}|${f}|${normRoom}`;
}

export function computeComplaintFingerprint(params = {}) {
  const catNorm = (params.category || "").trim().toLowerCase();
  const locKey = normalizeLocationKey(params);
  const issueTokens = normalizeIssueText(params.description || "", params.room_no || "");
  return `${catNorm}::${locKey}::${issueTokens}`;
}

export function isSimilarIssue(desc1, desc2, roomNo = "") {
  const tokens1 = new Set(normalizeIssueText(desc1, roomNo).split(" ").filter(Boolean));
  const tokens2 = new Set(normalizeIssueText(desc2, roomNo).split(" ").filter(Boolean));

  const ignoreWords = new Set(["not", "work", "break", "stop", "stopped", "fix", "repair", "issue", "problem", "fault", "faulty", "bad", "damage", "damaged"]);

  const meaningful1 = new Set([...tokens1].filter(x => !ignoreWords.has(x)));
  const meaningful2 = new Set([...tokens2].filter(x => !ignoreWords.has(x)));

  if (meaningful1.size > 0 && meaningful2.size > 0) {
    const intersection = [...meaningful1].filter(x => meaningful2.has(x));
    return intersection.length > 0;
  }

  if (tokens1.size === 0 || tokens2.size === 0) {
    return true;
  }

  const intersection = [...tokens1].filter(x => tokens2.has(x));
  return intersection.length > 0;
}
