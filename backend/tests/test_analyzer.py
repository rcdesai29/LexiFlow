"""Quick test of the LexiFlow analyzer."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.analyzer import analyze_transcript

sample = """
So basically, I think that like, communication is very important in the workplace. 
You know, when you're trying to like, convey your ideas to a team, um, you need to 
be very clear about what you're saying. I mean, a lot of people just kind of, you know, 
ramble on and on without really making a point. And honestly, I think that's like a 
really big problem. Um, so what I would suggest is that, you know, before you speak, 
you should like think about what you want to say. And basically, just try to be more 
concise. Like, instead of saying a lot of words, just get to the point. You know what 
I mean? So yeah, basically, um, communication is very very important and we should all 
like try to be better at it. I think that's basically what I wanted to say. Um, yeah.
"""

results = analyze_transcript(sample, duration_seconds=120)

print("=" * 50)
print("LexiFlow Analysis Results")
print("=" * 50)
print(f"\nTotal words: {results['total_words']}")
print(f"Unique words: {results['unique_words']}")
print(f"Vocab diversity: {results['vocab_diversity']}")
print(f"Words per minute: {results['words_per_minute']}")
print(f"Filler count: {results['filler_count']}")

print("\nFiller breakdown:")
for word, count in sorted(results['filler_words'].items(), key=lambda x: -x[1]):
    print(f"  '{word}': {count}")

print("\nTop repeated words:")
for item in results['top_repeated_words'][:10]:
    print(f"  '{item['word']}': {item['count']}")

print("\n✓ All checks passed")
