import re
import json
import os

markdown_path = r"e:\مشروع منصه همه\Himma_Unified_Repository_v1.1_FINAL\reference\derived\01_المحتوى_والتخطيط_المعتمد_لمنصة_همة.md"
with open(markdown_path, 'r', encoding='utf-8') as f:
    text = f.read()

items = []
current_item = {}

def add_item():
    if current_item:
        if 'kind' not in current_item:
            pass # skip
        else:
            items.append(dict(current_item))

import uuid

NAMESPACE_HIMMA = uuid.uuid5(uuid.NAMESPACE_DNS, "himma.education")

def normalize_arabic(text):
    return " ".join(text.split())

lines = text.split('\n')
current_text = []
current_type = None

for line in lines:
    line = line.strip()
    if line.startswith('### السؤال') or line.startswith('### النشاط الأساسي') or line.startswith('### تقوية'):
        if current_item:
            raw = '\\n'.join(current_text)
            current_item['raw_text'] = raw
            # extract skill
            skill_match = re.search(r'\\*\\*المهارة:\\*\\*\\s*(.+)', raw)
            if skill_match:
                skill_name = normalize_arabic(skill_match.group(1).strip())
                current_item['skill_key'] = str(uuid.uuid5(NAMESPACE_HIMMA, skill_name))
                current_item['skill_name'] = skill_name
            else:
                current_item['skill_key'] = str(uuid.uuid5(NAMESPACE_HIMMA, "مهارة عامة"))
                current_item['skill_name'] = "مهارة عامة"
            
            # create single step for now
            current_item['steps'] = [{
                "order_index": 1,
                "prompt_text": current_item['title'],
                "expected_reading_text": None,
                "options": [],
                "assets": []
            }]
            items.append(dict(current_item))
        
        current_item = {'version': '1.0', 'status': 'draft'}
        current_text = [line]
        title = line.replace('### ', '').strip()
        current_item['title'] = title
        current_item['stable_key'] = str(uuid.uuid5(NAMESPACE_HIMMA, title))
        if 'السؤال' in title:
            current_item['kind'] = 'question'
        elif 'النشاط الأساسي' in title:
            current_item['kind'] = 'core_activity'
        elif 'تقوية' in title:
            current_item['kind'] = 'reinforcement_activity'
    elif current_item:
        current_text.append(line)

if current_item:
    raw = '\\n'.join(current_text)
    current_item['raw_text'] = raw
    skill_match = re.search(r'\\*\\*المهارة:\\*\\*\\s*(.+)', raw)
    if skill_match:
        skill_name = normalize_arabic(skill_match.group(1).strip())
        current_item['skill_key'] = str(uuid.uuid5(NAMESPACE_HIMMA, skill_name))
        current_item['skill_name'] = skill_name
    else:
        current_item['skill_key'] = str(uuid.uuid5(NAMESPACE_HIMMA, "مهارة عامة"))
        current_item['skill_name'] = "مهارة عامة"
    
    current_item['steps'] = [{
        "order_index": 1,
        "prompt_text": current_item['title'],
        "expected_reading_text": None,
        "options": [],
        "assets": []
    }]
    items.append(dict(current_item))

with open(r'e:\\مشروع منصه همه\\Himma_Unified_Repository_v1.1_FINAL\\packages\\content\\src\\catalog.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(items)} items")
