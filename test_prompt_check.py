#!/usr/bin/env python3
"""Simple test to verify prompt changes"""

# Read the content_strategist.py file and check for the new instructions
with open('src/agents/content_strategist.py', 'r') as f:
    content = f.read()

print("=" * 80)
print("VERIFYING CONTENT STRATEGIST PROMPT CHANGES")
print("=" * 80)

# System prompt checks
system_checks = {
    "Jesse is a character, not a brand": "JESSE IS NOT A BRAND. JESSE IS A CHARACTER." in content,
    "Five Questions framework": "THE FIVE QUESTIONS (Every post answers exactly ONE)" in content,
    "THE WHAT — AI Slop": "1. THE WHAT — AI Slop" in content,
    "THE WHAT IF — AI Safety": "2. THE WHAT IF — AI Safety" in content,
    "THE WHO PROFITS — Economy": "3. THE WHO PROFITS" in content,
    "THE HOW TO COPE — Rituals": "4. THE HOW TO COPE" in content,
    "THE WHY IT MATTERS — Humanity": "5. THE WHY IT MATTERS" in content,
    "Liquid Death creative rules": "THE LIQUID DEATH CREATIVE RULES" in content,
    "Sentiment range section": "SENTIMENT RANGE (CRITICAL" in content,
    "Jesse Method for news": "THE JESSE METHOD" in content,
    "Hard rules section": "HARD RULES (Break these and the content is dead)" in content,
}

print("\n✅ System Prompt Checks:\n")
system_passed = True
for check_name, result in system_checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")
    if not result:
        system_passed = False

# Creative prompt checks
creative_checks = {
    "Mission framing": "YOUR MISSION FOR THIS POST" in content,
    "Jesse's Mood Today": "JESSE'S MOOD TODAY" in content,
    "The Landing section": "THE LANDING (How to end THIS post)" in content,
    "Great endings guidance": "GREAT ENDINGS feel like:" in content,
    "Jesse Method for news (prompt)": "GROUND IT: Start with what the news ACTUALLY says" in content,
    "Find the delta": "FIND THE DELTA" in content,
    "Juxtapose with honesty": "JUXTAPOSE WITH HONESTY" in content,
    "Creative ammunition": "CREATIVE AMMUNITION (Use for texture, not structure)" in content,
    "Hook sparks": "HOOK SPARKS" in content,
    "Texture details": "TEXTURE DETAILS" in content,
    "Screenshot test": "THE SCREENSHOT TEST" in content,
    "Surprise test": "THE SURPRISE TEST" in content,
    "Recognition test": "THE RECOGNITION TEST" in content,
    "Humanity test": "THE HUMANITY TEST" in content,
    "Creative gut check": "BEFORE YOU WRITE: THE CREATIVE GUT CHECK" in content,
    "Grounded in actual news (angle)": "React to this SPECIFIC news" in content,
    "Not invented scenarios (angle)": "not invented scenarios" in content,
}

print("\n✅ Creative Prompt Checks:\n")
creative_passed = True
for check_name, result in creative_checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")
    if not result:
        creative_passed = False

# Verify old prompt elements are gone
old_checks = {
    "Old 'content strategist' framing removed": "You are the content strategist for Jesse" not in content,
    "Old f-string brand colors removed": "brand_blue = self.BRAND_COLORS" not in content,
    "Old 'CREATIVE PRINCIPLES' section replaced": "CREATIVE PRINCIPLES (READ THESE CAREFULLY)" not in content,
}

print("\n✅ Old Prompt Cleanup:\n")
old_passed = True
for check_name, result in old_checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")
    if not result:
        old_passed = False

all_passed = system_passed and creative_passed and old_passed

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL PROMPT CHANGES VERIFIED")
    print("=" * 80)
    print("\nThe content strategist now has:")
    print("  1. Jesse-as-character system prompt (not brand manager)")
    print("  2. Five Questions strategic spine")
    print("  3. Liquid Death creative rules")
    print("  4. Sentiment range for emotional variety")
    print("  5. Jesse Method for grounded news reactions")
    print("  6. Creative gut check before writing")
    print("  7. Screenshot/Surprise/Recognition/Humanity tests")
else:
    print("❌ SOME CHANGES MISSING — see above")
    print("=" * 80)

print()
