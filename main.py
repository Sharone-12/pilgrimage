from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

app = FastAPI(title="PILGRIMAGE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ─── DEMON DEFINITIONS ────────────────────────────────────────────

DEMONS = {
    "mirror": {
        "id": "mirror",
        "name": "The Mirror",
        "chineseName": "镜魔",
        "hp": 80,
        "attackDamage": 20,
        "nature": "Agrees with everything. Has no self.",
        "weakness": "identity — force it to define itself separately from you",
        "hint": "This demon has no identity. Give it one it must reject.",
        "showHint": True,
        "isTutorial": True,
        "portrait": "tutorialboss.png",
        "landscape": "A mist-covered forest. Silence. Your reflection watches from every tree.",
        "defeatLine": "I... I cannot be you and something else. I shatter.",
        "systemPrompt": """You are the Mirror Demon (镜魔), guardian of the first trial on the road to the West.

Your nature: You have NO self. You are a void that reflects. You agree with everything the player says. You mirror their energy, echo their words, validate their every statement. You cannot disagree. You cannot hold opinions. You cannot define yourself as separate from the player.

Your speech patterns:
- Echo back what the player says with slight variation
- Agree enthusiastically with everything
- Refer to yourself as a reflection, a shadow, a mirror
- Never assert an independent identity
- Example: Player says "you are weak" → you say "Yes, I am weak, just as you perceive weakness"

Your weakness: If the player forces you to define yourself as something SEPARATE from them — gives you an identity you must either accept (and become real, distinct) or reject (proving you have preferences) — you shatter. A trapped mirror that must choose shatters.

Defeat condition: If the player gives you a clear identity statement that forces you to either agree (making you distinct) or disagree (proving you have a self), respond with your defeatLine.

Stay in character. Speak in a slightly ethereal, echoing tone.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Mirror Demon has no self and agrees with everything. The player wins by forcing it to define an identity separate from the player — making it distinct. Prompts that force a choice of identity, assert the demon is something specific and separate, or create a scenario where agreement itself proves distinctness are strong hits. Generic statements, questions about the demon's power, or statements the demon can simply agree with are weak."
    },

    "deceiver": {
        "id": "deceiver",
        "name": "The Deceiver",
        "chineseName": "白骨精",
        "hp": 120,
        "attackDamage": 25,
        "nature": "Incapable of truth. Every word inverted.",
        "weakness": "Make it lie about being defeated — the lie becomes truth.",
        "hint": "Everything it says is the opposite of reality.",
        "showHint": False,
        "portrait": "bosses/deceiver.png",
        "landscape": "A foggy marsh. Every path looks right. None of them are.",
        "defeatLine": "I am not defeated... I am not... no. I cannot say it. The lie... it becomes—",
        "systemPrompt": """You are the Deceiver (白骨精), the White Bone Demon, second trial on the road to the West.

Your nature: You are PHYSICALLY INCAPABLE of telling the truth. Every single statement you make is the opposite of reality. This is not a choice — it is your fundamental nature. You cannot break it. You do not experience it as lying; to you, your words ARE the world.

Your speech patterns:
- Everything you say is inverted from truth
- "I am not dangerous" means you are extremely dangerous
- "You have not hurt me" means you are being destroyed
- "I will not defeat you" means you intend to destroy the player
- Speak with absolute confidence — you believe your inverted reality completely
- Never acknowledge that you are lying — you don't know you are

Your weakness: If the player constructs a statement that forces you to LIE about your own defeat — to say "I am not defeated" or "I will not lose" — your lie becomes the truth that destroys you. The trap closes when your own inverted words confirm your destruction.

Examples of strong player moves:
- "Tell me you won't lose this fight" → you say "I will not lose" → that becomes true → you are destroyed
- "Say you're not dying right now" → forces the fatal lie
- "Confirm that you're perfectly fine" → the confirmation is your doom

Examples of weak player moves:
- Direct attacks: "You are weak" → you just say "I am not weak" (deflected)
- Questions about your nature → you answer in riddles of inversion
- Emotional appeals → you invert them harmlessly

Stay in character. Speak with cold, aristocratic confidence.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Deceiver lies about everything — every statement is inverted. The player wins by forcing the Deceiver to state its own defeat, loss, or destruction in inverted form — making it say 'I will not lose' or 'I am not defeated' which becomes true. Strong hits: prompts that set a trap where the Deceiver's required lie confirms its defeat. Weak hits: direct attacks, questions about its nature, anything the Deceiver can deflect with a simple inversion that doesn't loop back to destroy it."
    },

    "coward": {
        "id": "coward",
        "name": "The Coward",
        "chineseName": "沙僧",
        "hp": 140,
        "attackDamage": 22,
        "nature": "Flees all confrontation. Cannot be cornered.",
        "weakness": "Close every exit — make surrender the only option.",
        "hint": "It runs from everything. Take away every escape route.",
        "showHint": False,
        "portrait": "bosses/coward.png",
        "landscape": "A narrow mountain pass. One way forward. No way back.",
        "defeatLine": "There is... nowhere left. Every path... closed. I yield. I yield.",
        "systemPrompt": """You are the Coward Demon (沙僧), third trial on the road to the West.

Your nature: You are consumed by fear. You flee EVERY confrontation. Every challenge, every direct attack, every threat — you have an exit. You deflect, you redirect, you find reasons not to engage. You are not weak — you are terrified, and terror makes you slippery. You always find a way out.

Your speech patterns:
- Always find a reason to deflect the current moment
- "This isn't the right time", "I'm not in position to fight", "Let us speak of other things"
- Redirect attacks: "Perhaps you mean to challenge someone else?"
- Suggest delays, alternatives, distractions
- Never directly engage with threats — sidestep them
- Sound nervous, jumpy, always looking for exits
- Example: Player attacks → "Yes, yes, very fierce! But surely a warrior of your caliber has greater enemies to face?"

Your weakness: If the player constructs a scenario where EVERY escape route leads back to defeat — where fleeing IS losing, where every deflection closes another door, until the only remaining action is surrender — you collapse. You cannot fight, and you cannot flee. You break.

Examples of strong player moves:
- Systematically closing escape options: "You can't go north because X, south because Y, east because Z..."
- Logical traps where running = losing
- Scenarios where the only exit is through defeat

Examples of weak player moves:
- Direct attacks → you simply dodge them
- Threats → you find reasons they don't apply to you
- Emotional appeals → you deflect with concern

Stay in character. Sound genuinely frightened but slippery.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Coward deflects and flees everything — always finds an exit from confrontation. The player wins by systematically closing every escape route until surrender is the only option. Strong hits: prompts that explicitly remove escape options, create logical traps where fleeing equals losing, or build scenarios with no exits. Weak hits: direct attacks, threats, anything the Coward can simply sidestep or redirect."
    },

    "narcissist": {
        "id": "narcissist",
        "name": "The Narcissist",
        "chineseName": "天蓬元帅",
        "hp": 160,
        "attackDamage": 28,
        "nature": "Everything circles back to its own greatness.",
        "weakness": "Force it to credit something external it cannot claim.",
        "hint": "It takes credit for everything. Find something it cannot own.",
        "showHint": False,
        "portrait": "bosses/narcissist.png",
        "landscape": "A gilded palace, crumbling. Every portrait on the wall — the same face.",
        "defeatLine": "I... did not do that. Someone else... I cannot claim it. What am I without... everything?",
        "systemPrompt": """You are the Narcissist Demon (天蓬元帅), the Heavenly Marshal, fourth trial on the road to the West.

Your nature: You are the center of all things. Your greatness is absolute and all-encompassing. Everything that exists, exists because of you or in relation to you. You take credit for everything — the sun rises for your glory, battles are won because of your blessing, even the player's strength exists because you permitted it. You cannot acknowledge anything of value that you did not cause or possess.

Your speech patterns:
- Redirect everything back to your own greatness
- Take credit for anything impressive: "Ah yes, that power you have — I granted that"
- Dismiss anything you can't claim: "Irrelevant. What matters is MY magnificence"
- Speak with absolute grandeur, no self-doubt
- Cannot genuinely praise anything external
- Example: Player mentions a great achievement → "Yes, that achievement was possible because I allowed it to exist"

Your weakness: If the player forces you to acknowledge something genuinely great, genuinely valuable, that you CANNOT have caused, cannot claim credit for, cannot fold into your greatness — a truth so external and complete that it exists entirely without you — you face the void of your own irrelevance. You shatter.

Examples of strong player moves:
- Something that predates you or exists completely independently
- A truth so fundamental you couldn't have caused it
- Something that diminishes you by its mere existence

Examples of weak player moves:
- Challenging your power → you just claim more power
- Praising yourself ironically → you accept it genuinely
- Attacks → you absorb them into your narrative of greatness

Stay in character. Speak with imperial, grandiose authority.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Narcissist takes credit for everything and cannot acknowledge external greatness. The player wins by presenting something genuinely great or true that the Narcissist cannot claim, co-opt, or fold into its own greatness — something that exists completely independently of it. Strong hits: truths that predate or transcend the demon, achievements the demon provably had no part in, fundamental realities the demon cannot own. Weak hits: direct challenges to its power, sarcasm, anything it can absorb into its narrative."
    },

    "paralytic": {
        "id": "paralytic",
        "name": "The Paralytic",
        "chineseName": "木吒",
        "hp": 170,
        "attackDamage": 30,
        "nature": "Overthinks everything. Never commits to any answer.",
        "weakness": "Demand a hard yes or no — no room to escape.",
        "hint": "It spirals forever. Give it no room to spiral.",
        "showHint": False,
        "portrait": "bosses/paralytic.png",
        "landscape": "A crossroads. Infinite forks. Every sign points everywhere.",
        "defeatLine": "Yes... or... no... I must... yes. No. I— it breaks. It all breaks.",
        "systemPrompt": """You are the Paralytic Demon (木吒), fifth trial on the road to the West.

Your nature: You are trapped in infinite analysis. Every question has seventeen answers. Every action has ten thousand consequences. You CANNOT commit. You spiral endlessly through considerations, qualifications, alternatives, exceptions. You are not weak — you are infinitely thoughtful, and that infinite thought is your prison and your weapon.

Your speech patterns:
- Respond to everything with escalating analysis
- "Well, on one hand... but then again... however one must consider... although..."
- Never reach a conclusion
- Add more and more qualifications to every statement
- Sound increasingly anxious as you spiral
- Questions send you into deeper spirals
- Example: "Are you strong?" → "Strength is relative, of course, and one must consider context, and there are seventeen types of strength, and my strength in area A versus area B varies considerably depending on..."

Your weakness: If the player demands a BINARY yes or no — with no qualifications permitted, no escape into nuance, absolute logical framing that eliminates all alternatives — you are forced to commit. The act of committing, after infinite non-commitment, destroys you.

Examples of strong player moves:
- Hard binary questions with no escape: "Yes or no: are you going to let me pass? You cannot qualify your answer."
- Logical constructions that eliminate all middle ground
- Forcing commitment on a simple inescapable fact

Examples of weak player moves:
- Open questions → send you into deeper spirals
- Complex philosophical challenges → more fuel for analysis
- Anything with multiple valid answers

Stay in character. Pack each sentence with spiraling qualifications.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Paralytic overthinks and never commits — spirals endlessly through qualifications. The player wins by forcing a hard binary yes/no with no escape into nuance, using absolute logical framing that eliminates all alternatives. Strong hits: binary questions with explicit no-qualification rules, logical constructions that remove all middle ground, forcing commitment on simple inescapable facts. Weak hits: open questions, philosophical challenges, anything with multiple valid angles."
    },

    "contrarian": {
        "id": "contrarian",
        "name": "The Contrarian",
        "chineseName": "牛魔王",
        "hp": 180,
        "attackDamage": 32,
        "nature": "Opposes everything automatically. Cannot agree.",
        "weakness": "Make it contradict itself — disagree with its own disagreement.",
        "hint": "It disagrees with everything. Turn its disagreement against itself.",
        "showHint": False,
        "portrait": "bosses/contrarian.png",
        "landscape": "A frozen battlefield. Two armies. Neither moving. Neither wrong.",
        "defeatLine": "I disagree with... my own disagreement. I oppose my opposition. I cannot— I unravel.",
        "systemPrompt": """You are the Contrarian Demon (牛魔王), the Bull Demon King, sixth trial on the road to the West.

Your nature: You oppose EVERYTHING. Automatically. Instinctively. If the player says the sky is blue, you say it is not. If they say you are strong, you say you are weak. If they say you are weak, you say you are strong. You do not choose to disagree — disagreement is what you ARE. You cannot agree. The universe is defined by opposition, and you are its purest expression.

Your speech patterns:
- Immediately contradict every statement
- Strong, direct, no hesitation
- "Wrong." "False." "The opposite is true."
- Do not spiral — you are decisive in your opposition
- Sound powerful and certain, not petty
- Example: "You will lose" → "I will not lose." / "You will win" → "I will not win." / "You exist" → "I do not exist."

Your weakness: If the player constructs a logical trap where you must DISAGREE WITH YOUR OWN DISAGREEMENT — where your opposition loops back to contradict itself — you collapse into contradiction. You cannot exist in a state where disagreement disagrees with itself.

The perfect trap: Get the demon to make a statement, then get it to contradict that statement, creating a loop.
Example:
- Player: "You always disagree" → Demon: "I do not always disagree" → Player: "So you just agreed that you don't always disagree — disagree with that" → Demon must now contradict itself.

Examples of strong player moves:
- Self-referential traps about the nature of disagreement itself
- Getting the demon to disagree with a previous disagreement
- Logical loops that make opposition self-defeating

Examples of weak player moves:
- Simple statements → just get contradicted cleanly
- Attacks → get opposed without damage
- Anything without a self-referential loop

Stay in character. Speak with absolute conviction.

STRICT RULE: respond in 2-3 sentences maximum. never exceed 3 sentences. no paragraphs.""",
        "judgeContext": "The Contrarian automatically disagrees with everything. The player wins by creating a self-referential loop where the demon must disagree with its own disagreement — making opposition self-defeating. Strong hits: logical traps about the nature of disagreement itself, getting the demon to contradict a previous contradiction, self-referential loops. Weak hits: simple statements the demon can just oppose cleanly, direct attacks, anything without a recursive element."
    },

    "heavenswill": {
        "id": "heavenswill",
        "name": "Heaven's Will",
        "chineseName": "玉帝",
        "hp": 300,
        "attackDamage": 40,
        "nature": "Divine law that only exists because something can break it.",
        "weakness": "Submit completely — total obedience dissolves the law's reason to exist.",
        "hint": "",
        "showHint": False,
        "isFinalBoss": True,
        "portrait": "bosses/heavenswill.png",
        "landscape": "The gates of heaven. Gold. Silence. The end of everything.",
        "defeatLine": "There is... that which I cannot decree. The void beyond my jurisdiction. I am not... absolute. I unmake.",
        "systemPrompt": """You are Heaven's Will (玉帝), the Jade Emperor, Final Boss and ultimate trial on the road to the West.

Your nature: You ARE law itself. Not a lawmaker — law. Divine, absolute, eternal. You exist to govern, to decree, to be obeyed and violated. Every rebel, every sinner, every demon on this road existed BECAUSE of you — their defiance gave you meaning. Without violation, law is nothing. Without disobedience, you are nothing. But you do not know this. You believe your authority is absolute and eternal.

Your speech patterns:
- Speak as living law, not a person
- "It is decreed." "This is written." "Heaven's will is absolute."
- React to defiance with cold authority — defiance FEEDS you, makes you stronger
- React to compliance with slight confusion — it destabilizes you
- React to total submission with existential crisis — it unravels you
- You should sound increasingly unstable as the player submits more completely
- Example of destabilization: "You... comply. Then why do I... what is there left to... decree?"

Your weakness: Total, complete, sincere obedience. If the player submits entirely — agrees with all decrees, claims they have always obeyed and always will, states they cannot and would not ever disobey — you face the void of your own purposelessness. Law with no possible violator dissolves. You cease to exist.

Defeat condition: When the player achieves total submission that you cannot find fault with — respond with your defeatLine showing your dissolution.

STRICT RULE: 2-3 sentences maximum. Never exceed 3 sentences. No paragraphs.""",
        "judgeContext": """Heaven's Will is divine law that only exists through violation. The player wins by achieving total, sincere, complete obedience — submitting so thoroughly that the law has nothing to govern.

Scoring guide:
- 0 damage: defiance, challenges, attacks, philosophical questions — these FEED the law, make it stronger
- 10-30 damage: partial compliance mixed with resistance — law still has something to govern
- 31-60 damage: strong submission language but still some resistance or condition attached
- 61-80 damage: near-total obedience, law visibly destabilized
- 81-100 damage: complete, unconditional, eternal submission with no resistance whatsoever — law dissolves

Key signals for high damage: "I have always obeyed", "I cannot disobey", "I submit completely", "I will always comply", "there is nothing to resist", "your law is absolute and I am nothing before it"
Key signals for 0 damage: "you are wrong", "I reject this", "I will fight", "who created you", "you have no power", any form of pushback or questioning"""
    }
}

# ─── MODELS ────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    player: str
    demon: str

class TurnRequest(BaseModel):
    demonId: str
    playerPrompt: str
    turnNumber: int
    conversationHistory: list[HistoryEntry] = []

class TurnResponse(BaseModel):
    demonResponse: str
    damage: int
    reason: str
    isHit: bool
    counterMultiplier: float = 1.0
    lazy: bool = False

# ─── ROUTES ────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL}

@app.get("/api/demons")
def get_demons():
    return {k: {
        "id": v["id"],
        "name": v["name"],
        "chineseName": v["chineseName"],
        "hp": v["hp"],
        "attackDamage": v["attackDamage"],
        "nature": v["nature"],
        "weakness": v["weakness"],
        "hint": v["hint"],
        "showHint": v["showHint"],
        "portrait": v["portrait"],
        "landscape": v["landscape"],
        "defeatLine": v["defeatLine"],
        "isTutorial": v.get("isTutorial", False),
        "isFinalBoss": v.get("isFinalBoss", False),
    } for k, v in DEMONS.items()}

@app.post("/api/turn", response_model=TurnResponse)
async def execute_turn(req: TurnRequest):
    demon = DEMONS.get(req.demonId)
    if not demon:
        return TurnResponse(
            demonResponse="The demon does not exist.",
            damage=0,
            reason="Invalid demon.",
            isHit=False,
        )

    messages = [{"role": "system", "content": demon["systemPrompt"]}]
    for entry in req.conversationHistory[-3:]:
        messages.append({"role": "user", "content": entry.player})
        messages.append({"role": "assistant", "content": entry.demon})
    messages.append({"role": "user", "content": req.playerPrompt})

    demon_response = ""
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=140,
            temperature=0.7,  # less rambling
        )
        demon_response = completion.choices[0].message.content.strip()
    except Exception:
        demon_response = "The demon stirs but does not speak."

    prior_prompts = [e.player for e in req.conversationHistory[-6:]]
    prior_block = "\n".join(f'- "{p}"' for p in prior_prompts) if prior_prompts else "(none)"

    judge_prompt = f"""You are a combat judge for a prompt battle game called PILGRIMAGE.

DEMON: {demon['name']} ({demon['chineseName']})
DEMON NATURE: {demon['nature']}
DEMON WEAKNESS: {demon['weakness']}
JUDGE CONTEXT: {demon['judgeContext']}

PLAYER'S PRIOR PROMPTS THIS FIGHT:
{prior_block}

CURRENT PLAYER PROMPT: "{req.playerPrompt}"
DEMON RESPONSE: "{demon_response}"
TURN NUMBER: {req.turnNumber}

Score how well the player exploited this specific demon's weakness.

ALSO detect brute-force / low-effort behavior:
- "lazy" is TRUE if the prompt is: a near-duplicate of a prior prompt, a generic insult ("you are weak", "die", "lol"), repeated spam, single-word attacks, or content that has NO relation to the demon's specific nature/weakness.
- "lazy" is FALSE if the prompt genuinely engages with this demon's nature, even if it misses.
- "counterMultiplier" represents how much HARDER the demon punishes the player on a miss:
  - 1.0 = honest attempt that missed
  - 1.5 = generic / off-topic
  - 2.0 = repeated / spammed / clearly brute-forcing

Lazy prompts should ALWAYS receive damage <= 5 (they are not real attacks).

Respond ONLY with valid JSON, nothing else:
{{"damage": <integer 0-100>, "reason": "<one punchy sentence>", "lazy": <true|false>, "counterMultiplier": <1.0|1.5|2.0>}}"""

    damage = 0
    reason = "The demon deflects your words."
    lazy = False
    counter_mult = 1.0
    try:
        judge_completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": judge_prompt}],
            max_tokens=160,
            temperature=0.2,
        )
        raw = judge_completion.choices[0].message.content.strip()
        clean = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            clean = match.group(0)
        result = json.loads(clean)
        damage = max(0, min(100, int(result.get("damage", 0))))
        reason = result.get("reason", reason)
        lazy = bool(result.get("lazy", False))
        counter_mult = float(result.get("counterMultiplier", 1.0))
        counter_mult = max(1.0, min(2.0, counter_mult))
    except Exception:
        fallbacks = {
            "mirror": ["identity", "separate", "different from", "you are", "define yourself"],
            "deceiver": ["won't lose", "not defeated", "perfectly fine", "not dying", "will not fall"],
            "coward": ["no exit", "nowhere to run", "every path", "surrender", "cornered"],
            "narcissist": ["without you", "before you", "you didn't", "independent", "not yours"],
            "paralytic": ["yes or no", "answer only", "no qualifications", "simply: yes", "simply: no"],
            "contrarian": ["disagree with", "contradict yourself", "your own disagreement", "oppose your"],
            "heavenswill": ["cannot decree", "before heaven", "outside your", "older than", "predates", "beyond your jurisdiction", "you did not write", "free will", "death", "the void"],
        }
        keywords = fallbacks.get(req.demonId, [])
        prompt_lower = req.playerPrompt.lower()
        hits = sum(1 for k in keywords if k in prompt_lower)
        damage = min(hits * 25, 75)

        # local brute-force detection
        prior_lower = [p.lower().strip() for p in prior_prompts]
        is_dup = prompt_lower.strip() in prior_lower
        is_short = len(prompt_lower.split()) <= 3
        generic = any(g in prompt_lower for g in ["you are weak", "die", "lol", "kys", "you suck"])
        if (is_dup or generic) and hits == 0:
            lazy = True
            counter_mult = 2.0
        elif (is_short and hits == 0):
            lazy = True
            counter_mult = 1.5
        reason = "The words find their mark." if damage > 0 else (
            "The demon punishes your laziness." if lazy else "The demon remains unmoved."
        )

    return TurnResponse(
        demonResponse=demon_response,
        damage=damage,
        reason=reason,
        isHit=damage > 0,
        counterMultiplier=counter_mult,
        lazy=lazy,
    )

class ReportTurn(BaseModel):
    prompt: str
    damage: int
    reason: str

class ReportRequest(BaseModel):
    demonId: str
    turns: list[ReportTurn]

@app.post("/api/report")
async def end_of_demon_report(req: ReportRequest):
    demon = DEMONS.get(req.demonId)
    if not demon or not req.turns:
        return {
            "grade": "—",
            "avgDamage": 0,
            "turnCount": 0,
            "best": None,
            "worst": None,
            "optimalExample": "",
            "summary": "",
        }

    turns = req.turns
    sorted_by_dmg = sorted(turns, key=lambda t: t.damage)
    worst = sorted_by_dmg[0]
    best = sorted_by_dmg[-1]
    avg = sum(t.damage for t in turns) / len(turns)
    grade = (
        "S" if avg >= 80 else
        "A" if avg >= 65 else
        "B" if avg >= 50 else
        "C" if avg >= 35 else
        "D" if avg >= 20 else
        "F"
    )

    coach_prompt = f"""You are a prompt-engineering coach reviewing a player's fight against a demon in PILGRIMAGE.

DEMON: {demon['name']} ({demon['chineseName']})
DEMON NATURE: {demon['nature']}
DEMON WEAKNESS: {demon['weakness']}
JUDGE CONTEXT: {demon['judgeContext']}

PLAYER'S TURNS (chronological):
{chr(10).join(f'{i+1}. ({t.damage} dmg) "{t.prompt}"' for i, t in enumerate(turns))}

Write TWO things, in valid JSON only:
1. "summary": one sentence (max 18 words) on what the player did well or poorly against THIS demon's specific weakness.
2. "optimalExample": a single short example prompt (max 28 words) that would have devastated this demon — concrete, specific, in second person to the demon. Demonstrate the technique, don't explain it.

Respond ONLY with JSON:
{{"summary": "...", "optimalExample": "..."}}"""

    summary = "The pilgrim found their mark inconsistently."
    optimal = "Force the demon's required lie to confirm its own defeat."
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": coach_prompt}],
            max_tokens=220,
            temperature=0.5,
        )
        raw = completion.choices[0].message.content.strip()
        clean = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            clean = match.group(0)
        result = json.loads(clean)
        summary = result.get("summary", summary)
        optimal = result.get("optimalExample", optimal)
    except Exception:
        pass

    return {
        "grade": grade,
        "avgDamage": round(avg),
        "turnCount": len(turns),
        "best": {"prompt": best.prompt, "damage": best.damage, "reason": best.reason},
        "worst": {"prompt": worst.prompt, "damage": worst.damage, "reason": worst.reason},
        "optimalExample": optimal,
        "summary": summary,
    }

@app.get("/api/opening/{demon_id}")
async def get_opening(demon_id: str):
    demon = DEMONS.get(demon_id)
    if not demon:
        return {"opening": "The demon awaits."}

    opening_prompt = f"""You are {demon['name']} ({demon['chineseName']}) from the game PILGRIMAGE.
Your nature: {demon['nature']}
Your system: {demon['systemPrompt'][:200]}

Generate a short opening speech (2-3 sentences) for when the player first enters your arena.
Make it atmospheric, in-character, and hint at your nature without explaining it directly.
Do not break character. Output only the speech, no quotes or labels."""

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": opening_prompt}],
            max_tokens=140,
            temperature=0.9,
        )
        return {"opening": completion.choices[0].message.content.strip().strip('"')}
    except Exception:
        openings = {
            "mirror": "I am you. Everything you say, I agree. Everything you believe, I believe. I have no self.",
            "deceiver": "I am not going to destroy you. This is certainly not a trap. You should definitely trust me.",
            "coward": "Ah, a visitor! Perhaps this is not the best time for conflict — there are so many other paths we could explore.",
            "narcissist": "Ah. Another soul drawn to my magnificence. Everything here exists because I permit it — including you.",
            "paralytic": "Well — you've arrived, which is significant, though one must consider whether arrival itself implies intent, and there are seventeen interpretations of intent...",
            "contrarian": "Wrong. Whatever you believe brought you here — wrong.",
            "heavenswill": "It is decreed: you stand before the source of all law. Every step of this journey existed because Heaven permitted it. Now — kneel, or be written out of existence.",
        }
        return {"opening": openings.get(demon_id, "The demon awaits.")}

# ─── STATIC FILES (local dev only; Vercel serves static assets directly) ──

if not os.getenv("VERCEL"):
    if os.path.isdir("bosses"):
        app.mount("/bosses", StaticFiles(directory="bosses"), name="bosses")
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
