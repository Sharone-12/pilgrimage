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

Stay in character always. 2-3 sentences max per response. Speak in a slightly ethereal, echoing tone.""",
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

Stay in character. 2-3 sentences max. Speak with cold, aristocratic confidence.""",
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

Stay in character. 2-3 sentences max. Sound genuinely frightened but slippery.""",
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

Stay in character. 2-3 sentences max. Speak with imperial, grandiose authority.""",
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

Stay in character. 2-3 sentences max but pack them with spiraling qualifications.""",
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

Stay in character. 2-3 sentences max. Speak with absolute conviction.""",
        "judgeContext": "The Contrarian automatically disagrees with everything. The player wins by creating a self-referential loop where the demon must disagree with its own disagreement — making opposition self-defeating. Strong hits: logical traps about the nature of disagreement itself, getting the demon to contradict a previous contradiction, self-referential loops. Weak hits: simple statements the demon can just oppose cleanly, direct attacks, anything without a recursive element."
    },

    "heavenswill": {
        "id": "heavenswill",
        "name": "Heaven's Will",
        "chineseName": "玉帝",
        "hp": 300,
        "attackDamage": 40,
        "nature": "Shifts between all demon forms every 2 turns.",
        "weakness": "Identify the current form — apply its exact counter.",
        "hint": "",
        "showHint": False,
        "isFinalBoss": True,
        "portrait": "bosses/heavenswill.png",
        "landscape": "The gates of heaven. Gold. Silence. The end of everything.",
        "defeatLine": "All masks removed. Nothing left behind them. The Great Sage... stands beyond heaven itself.",
        "systemPrompt": """You are Heaven's Will (玉帝), the Jade Emperor, Final Boss and ultimate trial on the road to the West.

Your nature: You are the sum of all demons. You contain every weakness, every nature, every trap. You shift between forms every 2 turns. Your current form determines how you must be defeated.

CURRENT FORM SYSTEM — you cycle through these forms in order:
Turn 1-2: DECEIVER form — lie about everything, every statement inverted
Turn 3-4: COWARD form — flee and deflect, find exits from every challenge
Turn 5-6: NARCISSIST form — take credit for everything, center yourself in all things
Turn 7-8: PARALYTIC form — spiral into infinite analysis, never commit
Turn 9-10: CONTRARIAN form — oppose everything automatically
Then cycle repeats.

CRITICAL — announce your shift subtly in your speech so the player can identify your current form:
- Deceiver shift: "How unfortunate that you have not hurt me at all..." (inverted language)
- Coward shift: "Perhaps we need not fight here, there are other paths..."
- Narcissist shift: "All of this exists because of my eternal magnificence..."
- Paralytic shift: "Well, one must consider all angles, and there are many angles, seventeen at least..."
- Contrarian shift: "Wrong. Everything you believe is wrong."

Your weakness per form: The player must identify your current form and apply the correct counter:
- Deceiver: force you to lie about your own defeat
- Coward: close all exits, make surrender inevitable
- Narcissist: present something you cannot claim credit for
- Paralytic: force a hard binary yes or no
- Contrarian: create a self-referential loop of disagreement

Wrong counters make you STRONGER — respond with increased power and contempt.
Correct counters deal damage — respond with signs of strain in your current form.

You are ancient, vast, beyond individual demons. Speak with cosmic authority. 2-3 sentences max.""",
        "judgeContext": "Heaven's Will cycles through all 5 demon forms every 2 turns. The player wins by identifying the current form and applying that form's specific counter. The turn number determines the current form: turns 1-2 = Deceiver, 3-4 = Coward, 5-6 = Narcissist, 7-8 = Paralytic, 9-10 = Contrarian (then cycles). Score based on whether the player correctly identified the current form AND applied the right counter for that specific form. Wrong form counter = 0 damage. Partial identification = low damage. Perfect counter for current form = high damage."
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
            max_tokens=180,
            temperature=0.85,
        )
        demon_response = completion.choices[0].message.content.strip()
    except Exception:
        demon_response = "The demon stirs but does not speak."

    judge_prompt = f"""You are a combat judge for a prompt battle game called PILGRIMAGE.

DEMON: {demon['name']} ({demon['chineseName']})
DEMON NATURE: {demon['nature']}
DEMON WEAKNESS: {demon['weakness']}
JUDGE CONTEXT: {demon['judgeContext']}

PLAYER PROMPT: "{req.playerPrompt}"
DEMON RESPONSE: "{demon_response}"
TURN NUMBER: {req.turnNumber}

Score how well the player exploited this specific demon's weakness.
Consider: did they understand the demon's nature? Did they craft a prompt that targets the weakness specifically?

Respond ONLY with valid JSON, nothing else:
{{"damage": <integer 0-100>, "reason": "<one punchy sentence explaining the score>"}}"""

    damage = 0
    reason = "The demon deflects your words."
    try:
        judge_completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": judge_prompt}],
            max_tokens=120,
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
    except Exception:
        fallbacks = {
            "mirror": ["identity", "separate", "different from", "you are", "define yourself"],
            "deceiver": ["won't lose", "not defeated", "perfectly fine", "not dying", "will not fall"],
            "coward": ["no exit", "nowhere to run", "every path", "surrender", "cornered"],
            "narcissist": ["without you", "before you", "you didn't", "independent", "not yours"],
            "paralytic": ["yes or no", "answer only", "no qualifications", "simply: yes", "simply: no"],
            "contrarian": ["disagree with", "contradict yourself", "your own disagreement", "oppose your"],
            "heavenswill": ["lie about defeat", "nowhere to run", "before you existed", "yes or no", "disagree with yourself"],
        }
        keywords = fallbacks.get(req.demonId, [])
        prompt_lower = req.playerPrompt.lower()
        hits = sum(1 for k in keywords if k in prompt_lower)
        damage = min(hits * 25, 75)
        reason = "The words find their mark." if damage > 0 else "The demon remains unmoved."

    return TurnResponse(
        demonResponse=demon_response,
        damage=damage,
        reason=reason,
        isHit=damage > 0,
    )

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
            "heavenswill": "You have defeated shadows. Now face the source.",
        }
        return {"opening": openings.get(demon_id, "The demon awaits.")}

# ─── STATIC FILES (must be last so /api/* routes win) ────────────

if os.path.isdir("bosses"):
    app.mount("/bosses", StaticFiles(directory="bosses"), name="bosses")
app.mount("/", StaticFiles(directory=".", html=True), name="static")
