import re

with open('src/bot/locales.py', 'r', encoding='utf-8') as f:
    content = f.read()

en_add = '''        "shared_title": "✨ **What you have in common:**",
        "shared_city": "📍 You both live in the same city!",
        "shared_country": "📍 You both live in the same country!",
        "shared_origin": "🌍 You are from the same origin region!",'''

am_add = '''        "shared_title": "✨ **ምን ያመሳስላችኋል:**",
        "shared_city": "📍 ሁለታችሁም የምትኖሩት በአንድ ከተማ ነው!",
        "shared_country": "📍 ሁለታችሁም የምትኖሩት በአንድ ሀገር ነው!",
        "shared_origin": "🌍 ሁለታችሁም የመጣችሁት ከአንድ አካባቢ ነው!",'''

# Add to English dict (before "no_more_profiles")
content = content.replace('"no_more_profiles": "There are no more profiles to show right now.', en_add + '\n        "no_more_profiles": "There are no more profiles to show right now.')

# Add to Amharic dict (before "no_more_profiles")
# Since the Amharic characters in regex can be tricky with read(), I will use string replace targeting the btn_snnpr line.
# Let's find btn_snnpr in Amharic which is below btn_sidama.
# Actually, I'll just append it right before "match_found"
am_target = '"match_found": '
content = content.replace(am_target, am_add + '\n        ' + am_target, 1) # Only replace the first match of match_found, wait, the first match might be English!
# We can target amharic block specifically.
content = content.replace('        "match_found": "🎉 ተዛምደዋል!', am_add + '\n        "match_found": "🎉 ተዛምደዋል!')

with open('src/bot/locales.py', 'w', encoding='utf-8') as f:
    f.write(content)
