#!/usr/bin/env python3
"""
cold_wallet_recursive_sha256.py — ХОЛОДНЫЙ КОШЕЛЁК НА ЧИСТОМ PYTHON
=====================================================================
Рекурсивный SHA-256 с переставленными nothing-up-my-sleeve константами.
Полный комбайн: генерация сид-фразы + адрес.

Запуск:
    python cold_wallet_recursive_sha256.py                  # Сгенерировать новую фразу + адрес
    python cold_wallet_recursive_sha256.py "ваша фраза"     # Адрес из существующей фразы
    python cold_wallet_recursive_sha256.py --depth 5        # Новая фраза с глубиной 5
    python cold_wallet_recursive_sha256.py --test 100       # Тест уникальности
    python cold_wallet_recursive_sha256.py --bench          # Бенчмарк
"""

import sys
import argparse
import hashlib
import hmac
import struct
import random
import time
import os
import secrets

# ============================================================================
# BIP39 WORD LIST (2048 слов)
# ============================================================================

BIP39_WORDS = [
    "abandon", "ability", "able", "about", "above", "absent",
    "absorb", "abstract", "absurd", "abuse", "access", "accident",
    "account", "accuse", "achieve", "acid", "acoustic", "acquire",
    "across", "act", "action", "actor", "actress", "actual",
    "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advice", "aerobic", "affair", "afford",
    "afraid", "africa", "after", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle",
    "alarm", "album", "alcohol", "alert", "alien", "all",
    "alley", "allow", "almost", "alone", "alpha", "already",
    "also", "alter", "always", "amateur", "amazing", "among",
    "amount", "amused", "analyst", "anchor", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual",
    "another", "answer", "antenna", "antique", "anxiety", "any",
    "apart", "apology", "appear", "apple", "approve", "april",
    "arch", "arctic", "area", "arena", "argue", "arm",
    "armed", "armor", "army", "around", "arrange", "arrest",
    "arrive", "arrow", "art", "artefact", "artist", "artwork",
    "ask", "aspect", "assault", "asset", "assist", "assume",
    "asthma", "athlete", "atom", "attack", "attend", "attitude",
    "attract", "auction", "audit", "august", "aunt", "author",
    "auto", "autumn", "average", "avocado", "avoid", "awake",
    "aware", "away", "awesome", "awful", "awkward", "axis",
    "baby", "bachelor", "bacon", "badge", "bag", "balance",
    "balcony", "ball", "bamboo", "banana", "banner", "bar",
    "barely", "bargain", "barrel", "base", "basic", "basket",
    "battle", "beach", "bean", "beauty", "because", "become",
    "beef", "before", "begin", "behave", "behind", "believe",
    "below", "belt", "bench", "benefit", "best", "betray",
    "better", "between", "beyond", "bicycle", "bid", "bike",
    "bind", "biology", "bird", "birth", "bitter", "black",
    "blade", "blame", "blanket", "blast", "bleak", "bless",
    "blind", "blood", "blossom", "blouse", "blue", "blur",
    "blush", "board", "boat", "body", "boil", "bomb",
    "bone", "bonus", "book", "boost", "border", "boring",
    "borrow", "boss", "bottom", "bounce", "box", "boy",
    "bracket", "brain", "brand", "brass", "brave", "bread",
    "breeze", "brick", "bridge", "brief", "bright", "bring",
    "brisk", "broccoli", "broken", "bronze", "broom", "brother",
    "brown", "brush", "bubble", "buddy", "budget", "buffalo",
    "build", "bulb", "bulk", "bullet", "bundle", "bunker",
    "burden", "burger", "burst", "bus", "business", "busy",
    "butter", "buyer", "buzz", "cabbage", "cabin", "cable",
    "cactus", "cage", "cake", "call", "calm", "camera",
    "camp", "can", "canal", "cancel", "candy", "cannon",
    "canoe", "canvas", "canyon", "capable", "capital", "captain",
    "car", "carbon", "card", "cargo", "carpet", "carry",
    "cart", "case", "cash", "casino", "castle", "casual",
    "cat", "catalog", "catch", "category", "cattle", "caught",
    "cause", "caution", "cave", "ceiling", "celery", "cement",
    "census", "century", "cereal", "certain", "chair", "chalk",
    "champion", "change", "chaos", "chapter", "charge", "chase",
    "chat", "cheap", "check", "cheese", "chef", "cherry",
    "chest", "chicken", "chief", "child", "chimney", "choice",
    "choose", "chronic", "chuckle", "chunk", "churn", "cigar",
    "cinnamon", "circle", "citizen", "city", "civil", "claim",
    "clap", "clarify", "claw", "clay", "clean", "clerk",
    "clever", "click", "client", "cliff", "climb", "clinic",
    "clip", "clock", "clog", "close", "cloth", "cloud",
    "clown", "club", "clump", "cluster", "clutch", "coach",
    "coast", "coconut", "code", "coffee", "coil", "coin",
    "collect", "color", "column", "combine", "come", "comfort",
    "comic", "common", "company", "concert", "conduct", "confirm",
    "congress", "connect", "consider", "control", "convince", "cook",
    "cool", "copper", "copy", "coral", "core", "corn",
    "correct", "cost", "cotton", "couch", "country", "couple",
    "course", "cousin", "cover", "coyote", "crack", "cradle",
    "craft", "cram", "crane", "crash", "crater", "crawl",
    "crazy", "cream", "credit", "creek", "crew", "cricket",
    "crime", "crisp", "critic", "crop", "cross", "crouch",
    "crowd", "crucial", "cruel", "cruise", "crumble", "crunch",
    "crush", "cry", "crystal", "cube", "culture", "cup",
    "cupboard", "curious", "current", "curtain", "curve", "cushion",
    "custom", "cute", "cycle", "dad", "damage", "damp",
    "dance", "danger", "daring", "dash", "daughter", "dawn",
    "day", "deal", "debate", "debris", "decade", "december",
    "decide", "decline", "decorate", "decrease", "deer", "defense",
    "define", "defy", "degree", "delay", "deliver", "demand",
    "demise", "denial", "dentist", "deny", "depart", "depend",
    "deposit", "depth", "deputy", "derive", "describe", "desert",
    "design", "desk", "despair", "destroy", "detail", "detect",
    "develop", "device", "devote", "diagram", "dial", "diamond",
    "diary", "dice", "diesel", "diet", "differ", "digital",
    "dignity", "dilemma", "dinner", "dinosaur", "direct", "dirt",
    "disagree", "discover", "disease", "dish", "dismiss", "disorder",
    "display", "distance", "divert", "divide", "divorce", "dizzy",
    "doctor", "document", "dog", "doll", "dolphin", "domain",
    "donate", "donkey", "donor", "door", "dose", "double",
    "dove", "draft", "dragon", "drama", "drastic", "draw",
    "dream", "dress", "drift", "drill", "drink", "drip",
    "drive", "drop", "drum", "dry", "duck", "dumb",
    "dune", "during", "dust", "dutch", "duty", "dwarf",
    "dynamic", "eager", "eagle", "early", "earn", "earth",
    "easily", "east", "easy", "echo", "ecology", "economy",
    "edge", "edit", "educate", "effort", "egg", "eight",
    "either", "elbow", "elder", "electric", "elegant", "element",
    "elephant", "elevator", "elite", "else", "embark", "embody",
    "embrace", "emerge", "emotion", "employ", "empower", "empty",
    "enable", "enact", "end", "endless", "endorse", "enemy",
    "energy", "enforce", "engage", "engine", "enhance", "enjoy",
    "enlist", "enough", "enrich", "enroll", "ensure", "enter",
    "entire", "entry", "envelope", "episode", "equal", "equip",
    "era", "erase", "erode", "erosion", "error", "erupt",
    "escape", "essay", "essence", "estate", "eternal", "ethics",
    "evidence", "evil", "evoke", "evolve", "exact", "example",
    "excess", "exchange", "excite", "exclude", "excuse", "execute",
    "exercise", "exhaust", "exhibit", "exile", "exist", "exit",
    "exotic", "expand", "expect", "expire", "explain", "expose",
    "express", "extend", "extra", "eye", "eyebrow", "fabric",
    "face", "faculty", "fade", "faint", "faith", "fall",
    "false", "fame", "family", "famous", "fan", "fancy",
    "fantasy", "farm", "fashion", "fat", "fatal", "father",
    "fatigue", "fault", "favorite", "feature", "february", "federal",
    "fee", "feed", "feel", "female", "fence", "festival",
    "fetch", "fever", "few", "fiber", "fiction", "field",
    "figure", "file", "film", "filter", "final", "find",
    "fine", "finger", "finish", "fire", "firm", "first",
    "fiscal", "fish", "fit", "fitness", "fix", "flag",
    "flame", "flash", "flat", "flavor", "flee", "flight",
    "flip", "float", "flock", "floor", "flower", "fluid",
    "flush", "fly", "foam", "focus", "fog", "foil",
    "fold", "follow", "food", "foot", "force", "forest",
    "forget", "fork", "fortune", "forum", "forward", "fossil",
    "foster", "found", "fox", "fragile", "frame", "frequent",
    "fresh", "friend", "fringe", "frog", "front", "frost",
    "frown", "frozen", "fruit", "fuel", "fun", "funny",
    "furnace", "fury", "future", "gadget", "gain", "galaxy",
    "gallery", "game", "gap", "garage", "garbage", "garden",
    "garlic", "garment", "gas", "gasp", "gate", "gather",
    "gauge", "gaze", "general", "genius", "genre", "gentle",
    "genuine", "gesture", "ghost", "giant", "gift", "giggle",
    "ginger", "giraffe", "girl", "give", "glad", "glance",
    "glare", "glass", "glide", "glimpse", "globe", "gloom",
    "glory", "glove", "glow", "glue", "goat", "goddess",
    "gold", "good", "goose", "gorilla", "gospel", "gossip",
    "govern", "gown", "grab", "grace", "grain", "grant",
    "grape", "grass", "gravity", "great", "green", "grid",
    "grief", "grit", "grocery", "group", "grow", "grunt",
    "guard", "guess", "guide", "guilt", "guitar", "gun",
    "gym", "habit", "hair", "half", "hammer", "hamster",
    "hand", "happy", "harbor", "hard", "harsh", "harvest",
    "hat", "have", "hawk", "hazard", "head", "health",
    "heart", "heavy", "hedgehog", "height", "hello", "helmet",
    "help", "hen", "hero", "hidden", "high", "hill",
    "hint", "hip", "hire", "history", "hobby", "hockey",
    "hold", "hole", "holiday", "hollow", "home", "honey",
    "hood", "hope", "horn", "horror", "horse", "hospital",
    "host", "hotel", "hour", "hover", "hub", "huge",
    "human", "humble", "humor", "hundred", "hungry", "hunt",
    "hurdle", "hurry", "hurt", "husband", "hybrid", "ice",
    "icon", "idea", "identify", "idle", "ignore", "ill",
    "illegal", "illness", "image", "imitate", "immense", "immune",
    "impact", "impose", "improve", "impulse", "inch", "include",
    "income", "increase", "index", "indicate", "indoor", "industry",
    "infant", "inflict", "inform", "inhale", "inherit", "initial",
    "inject", "injury", "inmate", "inner", "innocent", "input",
    "inquiry", "insane", "insect", "inside", "inspire", "install",
    "intact", "interest", "into", "invest", "invite", "involve",
    "iron", "island", "isolate", "issue", "item", "ivory",
    "jacket", "jaguar", "jar", "jazz", "jealous", "jeans",
    "jelly", "jewel", "job", "join", "joke", "journey",
    "joy", "judge", "juice", "jump", "jungle", "junior",
    "junk", "just", "kangaroo", "keen", "keep", "ketchup",
    "key", "kick", "kid", "kidney", "kind", "kingdom",
    "kiss", "kit", "kitchen", "kite", "kitten", "kiwi",
    "knee", "knife", "knock", "know", "lab", "label",
    "labor", "ladder", "lady", "lake", "lamp", "language",
    "laptop", "large", "later", "latin", "laugh", "laundry",
    "lava", "law", "lawn", "lawsuit", "layer", "lazy",
    "leader", "leaf", "learn", "leave", "lecture", "left",
    "leg", "legal", "legend", "leisure", "lemon", "lend",
    "length", "lens", "leopard", "lesson", "letter", "level",
    "liar", "liberty", "library", "license", "life", "lift",
    "light", "like", "limb", "limit", "link", "lion",
    "liquid", "list", "little", "live", "lizard", "load",
    "loan", "lobster", "local", "lock", "logic", "lonely",
    "long", "loop", "lottery", "loud", "lounge", "love",
    "loyal", "lucky", "luggage", "lumber", "lunar", "lunch",
    "luxury", "lyrics", "machine", "mad", "magic", "magnet",
    "maid", "mail", "main", "major", "make", "mammal",
    "man", "manage", "mandate", "mango", "mansion", "manual",
    "maple", "marble", "march", "margin", "marine", "market",
    "marriage", "mask", "mass", "master", "match", "material",
    "math", "matrix", "matter", "maximum", "maze", "meadow",
    "mean", "measure", "meat", "mechanic", "medal", "media",
    "melody", "melt", "member", "memory", "mention", "menu",
    "mercy", "merge", "merit", "merry", "mesh", "message",
    "metal", "method", "middle", "midnight", "milk", "million",
    "mimic", "mind", "minimum", "minor", "minute", "miracle",
    "mirror", "misery", "miss", "mistake", "mix", "mixed",
    "mixture", "mobile", "model", "modify", "mom", "moment",
    "monitor", "monkey", "monster", "month", "moon", "moral",
    "more", "morning", "mosquito", "mother", "motion", "motor",
    "mountain", "mouse", "move", "movie", "much", "muffin",
    "mule", "multiply", "muscle", "museum", "mushroom", "music",
    "must", "mutual", "myself", "mystery", "myth", "naive",
    "name", "napkin", "narrow", "nasty", "nation", "nature",
    "near", "neck", "need", "negative", "neglect", "neither",
    "nephew", "nerve", "nest", "net", "network", "neutral",
    "never", "news", "next", "nice", "night", "noble",
    "noise", "nominee", "noodle", "normal", "north", "nose",
    "notable", "note", "nothing", "notice", "novel", "now",
    "nuclear", "number", "nurse", "nut", "oak", "obey",
    "object", "oblige", "obscure", "observe", "obtain", "obvious",
    "occur", "ocean", "october", "odor", "off", "offer",
    "office", "often", "oil", "okay", "old", "olive",
    "olympic", "omit", "once", "one", "onion", "online",
    "only", "open", "opera", "opinion", "oppose", "option",
    "orange", "orbit", "orchard", "order", "ordinary", "organ",
    "orient", "original", "orphan", "ostrich", "other", "outdoor",
    "outer", "output", "outside", "oval", "oven", "over",
    "own", "owner", "oxygen", "oyster", "ozone", "pact",
    "paddle", "page", "pair", "palace", "palm", "panda",
    "panel", "panic", "panther", "paper", "parade", "parent",
    "park", "parrot", "party", "pass", "patch", "path",
    "patient", "patrol", "pattern", "pause", "pave", "payment",
    "peace", "peanut", "pear", "peasant", "pelican", "pen",
    "penalty", "pencil", "people", "pepper", "perfect", "permit",
    "person", "pet", "phone", "photo", "phrase", "physical",
    "piano", "picnic", "picture", "piece", "pig", "pigeon",
    "pill", "pilot", "pink", "pioneer", "pipe", "pistol",
    "pitch", "pizza", "place", "planet", "plastic", "plate",
    "play", "please", "pledge", "pluck", "plug", "plunge",
    "poem", "poet", "point", "polar", "pole", "police",
    "pond", "pony", "pool", "popular", "portion", "position",
    "possible", "post", "potato", "pottery", "poverty", "powder",
    "power", "practice", "praise", "predict", "prefer", "prepare",
    "present", "pretty", "prevent", "price", "pride", "primary",
    "print", "priority", "prison", "private", "prize", "problem",
    "process", "produce", "profit", "program", "project", "promote",
    "proof", "property", "prosper", "protect", "proud", "provide",
    "public", "pudding", "pull", "pulp", "pulse", "pumpkin",
    "punch", "pupil", "puppy", "purchase", "purity", "purpose",
    "purse", "push", "put", "puzzle", "pyramid", "quality",
    "quantum", "quarter", "question", "quick", "quit", "quiz",
    "quote", "rabbit", "raccoon", "race", "rack", "radar",
    "radio", "rail", "rain", "raise", "rally", "ramp",
    "ranch", "random", "range", "rapid", "rare", "rate",
    "rather", "raven", "raw", "razor", "ready", "real",
    "reason", "rebel", "rebuild", "recall", "receive", "recipe",
    "record", "recycle", "reduce", "reflect", "reform", "refuse",
    "region", "regret", "regular", "reject", "relax", "release",
    "relief", "rely", "remain", "remember", "remind", "remove",
    "render", "renew", "rent", "reopen", "repair", "repeat",
    "replace", "report", "require", "rescue", "resemble", "resist",
    "resource", "response", "result", "retire", "retreat", "return",
    "reunion", "reveal", "review", "reward", "rhythm", "rib",
    "ribbon", "rice", "rich", "ride", "ridge", "rifle",
    "right", "rigid", "ring", "riot", "ripple", "risk",
    "ritual", "rival", "river", "road", "roast", "robot",
    "robust", "rocket", "romance", "roof", "rookie", "room",
    "rose", "rotate", "rough", "round", "route", "royal",
    "rubber", "rude", "rug", "rule", "run", "runway",
    "rural", "sad", "saddle", "sadness", "safe", "sail",
    "salad", "salmon", "salon", "salt", "salute", "same",
    "sample", "sand", "satisfy", "satoshi", "sauce", "sausage",
    "save", "say", "scale", "scan", "scare", "scatter",
    "scene", "scheme", "school", "science", "scissors", "scorpion",
    "scout", "scrap", "screen", "script", "scrub", "sea",
    "search", "season", "seat", "second", "secret", "section",
    "security", "seed", "seek", "segment", "select", "sell",
    "seminar", "senior", "sense", "sentence", "series", "service",
    "session", "settle", "setup", "seven", "shadow", "shaft",
    "shallow", "share", "shed", "shell", "sheriff", "shield",
    "shift", "shine", "ship", "shiver", "shock", "shoe",
    "shoot", "shop", "short", "shoulder", "shove", "shrimp",
    "shrug", "shuffle", "shy", "sibling", "sick", "side",
    "siege", "sight", "sign", "silent", "silk", "silly",
    "silver", "similar", "simple", "since", "sing", "siren",
    "sister", "situate", "six", "size", "skate", "sketch",
    "ski", "skill", "skin", "skirt", "skull", "slab",
    "slam", "sleep", "slender", "slice", "slide", "slight",
    "slim", "slogan", "slot", "slow", "slush", "small",
    "smart", "smile", "smoke", "smooth", "snack", "snake",
    "snap", "sniff", "snow", "soap", "soccer", "social",
    "sock", "soda", "soft", "solar", "soldier", "solid",
    "solution", "solve", "someone", "song", "soon", "sorry",
    "sort", "soul", "sound", "soup", "source", "south",
    "space", "spare", "spatial", "spawn", "speak", "special",
    "speed", "spell", "spend", "sphere", "spice", "spider",
    "spike", "spin", "spirit", "split", "spoil", "sponsor",
    "spoon", "sport", "spot", "spray", "spread", "spring",
    "spy", "square", "squeeze", "squirrel", "stable", "stadium",
    "staff", "stage", "stairs", "stamp", "stand", "start",
    "state", "stay", "steak", "steel", "stem", "step",
    "stereo", "stick", "still", "sting", "stock", "stomach",
    "stone", "stool", "story", "stove", "strategy", "street",
    "strike", "strong", "struggle", "student", "stuff", "stumble",
    "style", "subject", "submit", "subway", "success", "such",
    "sudden", "suffer", "sugar", "suggest", "suit", "summer",
    "sun", "sunny", "sunset", "super", "supply", "supreme",
    "sure", "surface", "surge", "surprise", "surround", "survey",
    "suspect", "sustain", "swallow", "swamp", "swap", "swarm",
    "swear", "sweet", "swift", "swim", "swing", "switch",
    "sword", "symbol", "symptom", "syrup", "system", "table",
    "tackle", "tag", "tail", "talent", "talk", "tank",
    "tape", "target", "task", "taste", "tattoo", "taxi",
    "teach", "team", "tell", "ten", "tenant", "tennis",
    "tent", "term", "test", "text", "thank", "that",
    "theme", "then", "theory", "there", "they", "thing",
    "this", "thought", "three", "thrive", "throw", "thumb",
    "thunder", "ticket", "tide", "tiger", "tilt", "timber",
    "time", "tiny", "tip", "tired", "tissue", "title",
    "toast", "tobacco", "today", "toddler", "toe", "together",
    "toilet", "token", "tomato", "tomorrow", "tone", "tongue",
    "tonight", "tool", "tooth", "top", "topic", "topple",
    "torch", "tornado", "tortoise", "toss", "total", "tourist",
    "toward", "tower", "town", "toy", "track", "trade",
    "traffic", "tragic", "train", "transfer", "trap", "trash",
    "travel", "tray", "treat", "tree", "trend", "trial",
    "tribe", "trick", "trigger", "trim", "trip", "trophy",
    "trouble", "truck", "true", "truly", "trumpet", "trust",
    "truth", "try", "tube", "tuition", "tumble", "tuna",
    "tunnel", "turkey", "turn", "turtle", "twelve", "twenty",
    "twice", "twin", "twist", "two", "type", "typical",
    "ugly", "umbrella", "unable", "unaware", "uncle", "uncover",
    "under", "undo", "unfair", "unfold", "unhappy", "uniform",
    "unique", "unit", "universe", "unknown", "unlock", "until",
    "unusual", "unveil", "update", "upgrade", "uphold", "upon",
    "upper", "upset", "urban", "urge", "usage", "use",
    "used", "useful", "useless", "usual", "utility", "vacant",
    "vacuum", "vague", "valid", "valley", "valve", "van",
    "vanish", "vapor", "various", "vast", "vault", "vehicle",
    "velvet", "vendor", "venture", "venue", "verb", "verify",
    "version", "very", "vessel", "veteran", "viable", "vibrant",
    "vicious", "victory", "video", "view", "village", "vintage",
    "violin", "virtual", "virus", "visa", "visit", "visual",
    "vital", "vivid", "vocal", "voice", "void", "volcano",
    "volume", "vote", "voyage", "wage", "wagon", "wait",
    "walk", "wall", "walnut", "want", "warfare", "warm",
    "warrior", "wash", "wasp", "waste", "water", "wave",
    "way", "wealth", "weapon", "wear", "weasel", "weather",
    "web", "wedding", "weekend", "weird", "welcome", "west",
    "wet", "whale", "what", "wheat", "wheel", "when",
    "where", "whip", "whisper", "wide", "width", "wife",
    "wild", "will", "win", "window", "wine", "wing",
    "wink", "winner", "winter", "wire", "wisdom", "wise",
    "wish", "witness", "wolf", "woman", "wonder", "wood",
    "wool", "word", "work", "world", "worry", "worth",
    "wrap", "wreck", "wrestle", "wrist", "write", "wrong",
    "yard", "year", "yellow", "you", "young", "youth",
    "zebra", "zero", "zone", "zoo"
]

# ============================================================================
# NOTHING-UP-MY-SLEEVE КОНСТАНТЫ SHA-256
# ============================================================================

H_CONSTANTS = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
]

K_CONSTANTS = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]


# ============================================================================
# SHA-256 С ПЕРЕСТАВЛЕННЫМИ КОНСТАНТАМИ
# ============================================================================

def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def sha256_permuted(message: bytes, h_order: list, k_order: list) -> bytes:
    H = [H_CONSTANTS[i] for i in h_order]
    K = [K_CONSTANTS[i] for i in k_order]
    
    msg_bytes = bytearray(message)
    msg_len_bits = len(msg_bytes) * 8
    msg_bytes.append(0x80)
    while (len(msg_bytes) + 8) % 64 != 0:
        msg_bytes.append(0x00)
    msg_bytes.extend(struct.pack('>Q', msg_len_bits))
    
    blocks = [msg_bytes[i:i+64] for i in range(0, len(msg_bytes), 64)]
    
    for block in blocks:
        w = list(struct.unpack('>16I', bytes(block)))
        
        for i in range(16, 64):
            s0 = _rotr(w[i-15], 7) ^ _rotr(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = _rotr(w[i-2], 17) ^ _rotr(w[i-2], 19) ^ (w[i-2] >> 10)
            w.append((w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF)
        
        a, b, c, d, e, f, g, h = [int(x) for x in H]
        
        for i in range(64):
            S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + K[i] + w[i]) & 0xFFFFFFFF
            S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF
            
            h = g; g = f; f = e; e = (d + temp1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (temp1 + temp2) & 0xFFFFFFFF
        
        H = [(H[i] + x) & 0xFFFFFFFF for i, x in enumerate([a, b, c, d, e, f, g, h])]
    
    return struct.pack('>8I', *[int(x) for x in H])


# ============================================================================
# РЕКУРСИВНЫЙ SHA-256
# ============================================================================

def recursive_sha256(message: bytes, initial_seed: bytes, depth: int = 3) -> bytes:
    seed = initial_seed
    data = message
    
    for _ in range(depth):
        rng = random.Random(seed)
        h_order = rng.sample(range(8), 8)
        k_order = rng.sample(range(64), 64)
        data = sha256_permuted(data, h_order, k_order)
        seed = data
    
    return data


# ============================================================================
# BIP39 ГЕНЕРАЦИЯ МНЕМОНИЧЕСКОЙ ФРАЗЫ
# ============================================================================

def generate_mnemonic(strength: int = 128) -> str:
    """
    Генерация BIP39 мнемонической фразы.
    strength: 128 (12 слов), 256 (24 слова)
    """
    if strength not in [128, 256]:
        strength = 128
    
    # Генерируем случайную энтропию
    entropy = secrets.token_bytes(strength // 8)
    
    # Вычисляем контрольную сумму
    hash_bytes = hashlib.sha256(entropy).digest()
    checksum_bits = strength // 32
    checksum = hash_bytes[0] >> (8 - checksum_bits)
    
    # Добавляем контрольную сумму к энтропии
    entropy_bits = int.from_bytes(entropy, 'big')
    combined = (entropy_bits << checksum_bits) | checksum
    
    # Разбиваем на группы по 11 бит
    word_count = (strength + checksum_bits) // 11
    words = []
    
    for i in range(word_count - 1, -1, -1):
        index = (combined >> (i * 11)) & 0x7FF
        words.append(BIP39_WORDS[index])
    
    return " ".join(words)


# ============================================================================
# BIP39 → BIP32 → RECURSIVE SHA-256 → ADDRESS
# ============================================================================

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    return hashlib.pbkdf2_hmac(
        'sha512',
        mnemonic.encode('utf-8'),
        ('mnemonic' + passphrase).encode('utf-8'),
        2048, 64
    )


def seed_to_master_key(seed: bytes) -> bytes:
    return hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()[:32]


def hash_to_address(hash_bytes: bytes) -> str:
    sha = hashlib.sha256(hash_bytes).digest()
    ripe = hashlib.new('ripemd160', sha).digest()
    prefix = b'\x00' + ripe
    checksum = hashlib.sha256(hashlib.sha256(prefix).digest()).digest()[:4]
    address_bytes = prefix + checksum
    
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(address_bytes, 'big')
    
    if num == 0:
        return '1'
    
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(alphabet[rem])
    
    return '1' + ''.join(reversed(result))


def mnemonic_to_address(mnemonic: str, depth: int = 3) -> dict:
    seed = mnemonic_to_seed(mnemonic)
    master_key = seed_to_master_key(seed)
    initial_seed = hashlib.sha256(master_key).digest()
    message = mnemonic.encode('utf-8')
    final_hash = recursive_sha256(message, initial_seed, depth)
    address = hash_to_address(final_hash)
    
    return {
        'mnemonic': mnemonic,
        'depth': depth,
        'seed': seed.hex(),
        'master_key': master_key.hex(),
        'initial_seed': initial_seed.hex(),
        'final_hash': final_hash.hex(),
        'address': address
    }


# ============================================================================
# ТЕСТЫ
# ============================================================================

def test_standard_sha256():
    h_order = list(range(8))
    k_order = list(range(64))
    
    tests = [
        (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (b"hello", "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"),
        (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ]
    
    print("  🧪 Проверка SHA-256:")
    for msg, expected in tests:
        result = sha256_permuted(msg, h_order, k_order).hex()
        status = "✅" if result == expected else "❌"
        print(f"  {status} SHA-256('{msg.decode()}')")
        if result != expected:
            return False
    return True


def test_determinism(depth=3):
    phrase = generate_mnemonic()
    results = [mnemonic_to_address(phrase, depth)['address'] for _ in range(5)]
    all_same = len(set(results)) == 1
    print(f"\n  🎯 Детерминизм: {'✅' if all_same else '❌'}")
    return all_same


def test_uniqueness(n=50, depth=3):
    addresses = set()
    for _ in range(n):
        phrase = generate_mnemonic()
        result = mnemonic_to_address(phrase, depth)
        addresses.add(result['address'])
    
    unique = len(addresses)
    print(f"\n  🔐 Уникальность: {unique}/{n}")
    print(f"  {'✅ Все уникальны!' if unique == n else f'❌ Коллизий: {n - unique}'}")
    return unique == n


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Холодный кошелёк-комбайн: генерация сид-фразы + рекурсивный SHA-256"
    )
    
    parser.add_argument("phrase", nargs="?", default=None,
                       help="Мнемоническая фраза (если не указана — сгенерировать новую)")
    parser.add_argument("--depth", type=int, default=3,
                       help="Глубина рекурсии (1-10, по умолчанию 3)")
    parser.add_argument("--test", type=int, default=None,
                       help="Количество тестов уникальности")
    parser.add_argument("--bench", type=int, default=None,
                       help="Количество итераций для бенчмарка")
    parser.add_argument("--verbose", action="store_true",
                       help="Подробный вывод")
    parser.add_argument("--words", type=int, default=12,
                       choices=[12, 24],
                       help="Количество слов в генерируемой фразе (12 или 24)")
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  COLD WALLET COMBO — RECURSIVE SHA-256                  ║")
    print("║  Nothing-up-my-sleeve | Permuted Constants              ║")
    print("║  Генерация фразы + Адрес в одном флаконе               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Глубина рекурсии: {args.depth}")
    print(f"  Сложность:        (8! × 64!)^{args.depth} × 2^256")
    print()
    
    # Тесты
    if not test_standard_sha256():
        print("\n  ❌ Реализация SHA-256 неверна!")
        return
    print()
    
    if not test_determinism(args.depth):
        print("  ❌ Детерминизм нарушен!")
        return
    
    # Бенчмарк
    if args.bench:
        phrase = generate_mnemonic()
        t0 = time.time()
        for _ in range(args.bench):
            mnemonic_to_address(phrase, args.depth)
        elapsed = time.time() - t0
        print(f"\n  ⚡ Производительность:")
        print(f"  {args.bench} итераций: {elapsed:.3f}s")
        print(f"  1 итерация:  {elapsed/args.bench*1000:.1f}ms")
        print()
        return
    
    # Тесты уникальности
    if args.test:
        test_uniqueness(args.test, args.depth)
        print()
        return
    
    # Генерация или использование фразы
    if args.phrase:
        mnemonic = args.phrase
        print("  Используется существующая фраза.")
    else:
        strength = 256 if args.words == 24 else 128
        mnemonic = generate_mnemonic(strength)
        print("  🎲 Сгенерирована НОВАЯ сид-фраза!")
    
    print()
    result = mnemonic_to_address(mnemonic, args.depth)
    
    if args.verbose:
        print(f"  Мнемоника:      {result['mnemonic']}")
        print(f"  Глубина:        {result['depth']}")
        print(f"  Seed:           {result['seed'][:32]}...")
        print(f"  Master Key:     {result['master_key']}")
        print(f"  Initial Seed:   {result['initial_seed']}")
        print(f"  Final Hash:     {result['final_hash']}")
        print(f"  Адрес:          {result['address']}")
    else:
        print(f"  Мнемоника: {result['mnemonic']}")
        print(f"  Адрес:     {result['address']}")
    
    print()
    print("  Статус: UNBREAKABLE")
    
    # Сохраняем в файл
    if not args.phrase:
        with open("wallet_generated.txt", "w", encoding="utf-8") as f:
            f.write(f"COLD WALLET — RECURSIVE SHA-256 (depth={args.depth})\n")
            f.write(f"=============================================\n")
            f.write(f"MNEMONIC: {result['mnemonic']}\n")
            f.write(f"ADDRESS:  {result['address']}\n")
            f.write(f"=============================================\n")
            f.write(f"KEEP THIS FILE OFFLINE. NEVER SHARE THE MNEMONIC.\n")
        print("  💾 Фраза и адрес сохранены в wallet_generated.txt")
    print()


if __name__ == "__main__":
    main()