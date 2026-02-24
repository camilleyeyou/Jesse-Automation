#!/usr/bin/env python3
"""Simple test to verify prompt changes"""

# Read the content_strategist.py file and check for the new instructions
with open('src/agents/content_strategist.py', 'r') as f:
    content = f.read()

print("=" * 80)
print("VERIFYING CONTENT GENERATOR PROMPT CHANGES")
print("=" * 80)

checks = {
    "GROUNDED NEWS COMMENTARY": "GROUNDED NEWS COMMENTARY" in content,
    "REFERENCE THE ACTUAL HEADLINE": "REFERENCE THE ACTUAL HEADLINE" in content,
    "BE SPECIFIC": "BE SPECIFIC: Use the real headline" in content,
    "FIND THE GAP": "FIND THE GAP: The absurdism comes from the delta" in content,
    "AVOID Picture this": "AVOID \"Picture this...\" or invented scenarios" in content,
    "React to REAL news": "React to the REAL news with deadpan specificity" in content,
    "Grounded in actual news (angle)": "React to this SPECIFIC news" in content,
    "Not invented scenarios (angle)": "not invented scenarios" in content,
}

print("\n✅ Checking new grounding instructions:\n")
all_passed = True
for check_name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")
    if not result:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL PROMPT CHANGES VERIFIED")
    print("=" * 80)
    print("\nThe content generator now has instructions to:")
    print("  1. Reference actual headlines (not invented scenarios)")
    print("  2. Be specific with real claims and numbers")
    print("  3. Find gaps between claims and reality")
    print("  4. Avoid 'Picture this...' generic observations")
    print("  5. Stay grounded in the real news story")
    print("\n⏳ NEXT: Container rebuild needed for RSS sources")
    print("   Once feedparser installed → Real HuggingFace/Simon Willison content")
    print("   + These prompt fixes = Specific news commentary")
else:
    print("❌ SOME CHANGES MISSING")
    print("=" * 80)
    
print()
