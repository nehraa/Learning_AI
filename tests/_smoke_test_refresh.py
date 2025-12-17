from app import EnhancedSystem
import json

s = EnhancedSystem()
# set some topics
s.user_prefs.set_topics(['machine learning', 'quantum consciousness'])
# first refresh
items1 = s.daily_discovery(s.user_prefs.prefs['topics'])
ids1 = [i['id'] for i in items1[:8]]
print('first ids:', ids1)
# second refresh should vary due to sampling
items2 = s.daily_discovery(s.user_prefs.prefs['topics'])
ids2 = [i['id'] for i in items2[:8]]
print('second ids:', ids2)

# show whether different
print('different:', ids1 != ids2)
