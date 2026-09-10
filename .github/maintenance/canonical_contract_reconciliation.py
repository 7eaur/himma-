from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# 1) Canonical source: approved visible stimuli + generated L3 sequence media.
path = Path("services/api/content_approval_contract_2026_09_08.py")
text = path.read_text(encoding="utf-8")
marker = "\n\nPOSTTEST_QUESTIONS = {"
visible = '''

# Student Experience R2 fields that were not changed by the Sep-08 wording
# approval. Keeping them here makes the final canonical release self-contained;
# runtime never imports the retired DB projection seeder.
LEARNING_VISIBLE_STIMULI = {
    "L1-CORE-01":["ب","ج","س","ق","د"],
    "L1-CORE-03":["ب","م","س","ك","ل"],
    "L1-CORE-07":["ب","كِتَاب","ذَهَبَ سَالِمٌ.","م","شَجَرَة"],
    "L1-REIN-01":["ب","ج","س","ق","د"],
    "L2-REIN-01":["_اب","ق_م","س_ك","كِتَا_","نُ_ر"],
    "L3-CORE-09":["هَادِئ","أَعَادَ","مُخَلَّفَات","صَافِيَة","قُرْبَ"],
    "L3-REIN-02":["المطر","اهتمام مريم","حفاظ خالد على الكتب"],
}

POSTTEST_QUESTIONS = {'''
text = replace_once(text, marker, visible, "visible stimuli insertion")
media_anchor = '    "POST-Q05":{1:[('
l3_media = '''    "L3-REIN-10":{
        1:[("SEQ-07","image","choice","أخذ الكتاب"),("SEQ-08","image","choice","قرأ الكتاب")],
        2:[("SEQ-01","image","choice","زرعت البذرة"),("SEQ-02","image","choice","سقتها")],
        3:[("HIMMA-GEN-SEQ-007","image","choice","دخول المكتبة"),("SEQ-08","image","choice","القراءة"),("SEQ-09","image","choice","إعادة الكتاب")],
        4:[("HIMMA-GEN-SEQ-008","image","choice","ذهب"),("HIMMA-GEN-SEQ-009","image","choice","لعب"),("HIMMA-GEN-SEQ-010","image","choice","نظف")],
        5:[("SEQ-04","image","choice","غسلت"),("SEQ-05","image","choice","قطعت"),("SEQ-06","image","choice","أكلت")],
    },
    "POST-Q05":{1:[('''
text = replace_once(text, media_anchor, l3_media, "L3 generated media insertion")
path.write_text(text, encoding="utf-8")

# 2) Compiler: fold approved Student Experience corrections into canonical release.
path = Path("services/api/canonical_content_compiler.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "    LEARNING_ROUND_STIMULI,\n",
    "    LEARNING_ROUND_STIMULI,\n    LEARNING_VISIBLE_STIMULI,\n",
    "compiler import",
)
old = '''    for canonical, correction in (payload.get("explicit_corrections") or {}).items():
        if canonical in items and correction.get("interaction"):
            items[canonical]["interaction_type"] = str(correction["interaction"])
'''
new = '''    corrections = payload.get("explicit_corrections") or {}
    for canonical, correction in corrections.items():
        if canonical not in items:
            continue
        if correction.get("interaction"):
            items[canonical]["interaction_type"] = str(correction["interaction"])
        if correction.get("title"):
            items[canonical]["title"] = str(correction["title"])

    # Student Experience v2 explicitly reconciled POST-Q14 to the pictured word
    # نَخْلَة. Sep-08 did not replace this field, so carry the approved sequence
    # into the single canonical source instead of falling back to legacy text.
    post_q14 = corrections.get("POST-Q14") or {}
    sequence = [str(value) for value in post_q14.get("answer_sequence") or []]
    if sequence:
        if len(sequence) != 4 or "".join(sequence) != "نخلة":
            raise RuntimeError(f"POST-Q14 approved answer sequence is invalid: {sequence}")
        step = items["POST-Q14"]["rounds"][0]
        step["options"] = [{"text": value, "is_correct": False} for value in sequence]
        items["POST-Q14"]["criterion"] = " ثم ".join(sequence)
'''
text = replace_once(text, old, new, "student v2 correction fold")
old = '''    for canonical, rounds in OPTION_CONTRACTS.items():
'''
new = '''    for canonical, values in LEARNING_VISIBLE_STIMULI.items():
        item = items[canonical]
        if len(item["rounds"]) != len(values):
            raise RuntimeError(f"{canonical}: visible stimulus round count mismatch")
        for step, value in zip(item["rounds"], values, strict=True):
            step["stimulus"] = {"kind": "text", "text": str(value)}

    for canonical, rounds in OPTION_CONTRACTS.items():
'''
text = replace_once(text, old, new, "visible stimulus compiler fold")
path.write_text(text, encoding="utf-8")

# 3) Media guard: explicit approved aliases only, no fuzzy matching.
path = Path("services/api/canonical_media_guard.py")
text = path.read_text(encoding="utf-8")
old = '''IMAGE_SEMANTIC_ALIASES: dict[str, set[str]] = {
    "SEQ-03": {"نمو الزهرة", "ظهور النبتة"},
    "SEQ-08": {"قراءة الكتاب", "القراءة"},
}
'''
new = '''IMAGE_SEMANTIC_ALIASES: dict[str, set[str]] = {
    "SEQ-01": {"زرع البذرة", "زرعت البذرة"},
    "SEQ-02": {"سقي البذرة", "سقتها"},
    "SEQ-03": {"نمو الزهرة", "ظهور النبتة"},
    "SEQ-04": {"غسل التفاحة", "غسلت"},
    "SEQ-05": {"تقطيع التفاحة", "قطعت"},
    "SEQ-06": {"أكل التفاحة", "أكلت"},
    "SEQ-07": {"إخراج الكتاب", "أخذ الكتاب"},
    "SEQ-08": {"قراءة الكتاب", "القراءة", "قرأ الكتاب"},
    "HIMMA-GEN-SEQ-008": {"الذهاب إلى الشاطئ", "ذهب ماجد إلى الشاطئ", "ذهب"},
    "HIMMA-GEN-SEQ-009": {"اللعب بالرمل", "لعب بالرمل", "لعب"},
    "HIMMA-GEN-SEQ-010": {"تنظيف المكان", "نظف مكانه", "نظف"},
}
'''
text = replace_once(text, old, new, "image semantic aliases")
path.write_text(text, encoding="utf-8")

# 4) Audio runtime tests: pending/rejected STEP must not resurface until explicit open.
path = Path("services/api/test_activity_audio_runtime.py")
text = path.read_text(encoding="utf-8")
old = '        assert current.json()["item"]["id"] != item_id\n'
if text.count(old) != 2:
    raise SystemExit(f"audio runtime step assertion: expected 2 matches, found {text.count(old)}")
text = text.replace(old, '        assert current.json()["step"]["id"] != step_id\n')
path.write_text(text, encoding="utf-8")

# 5) Canonical compiler listening test: story audio is item-context only.
path = Path("services/api/test_canonical_content_compiler.py")
text = path.read_text(encoding="utf-8")
old = '''            if sequences is not None:
                targets = sequences[int(step["order_index"]) - 1]
'''
new = '''            intro = item.get("context_intro") or {}
            if intro.get("kind") == "audio_story":
                assert prompt_audio == []
                continue
            if sequences is not None:
                targets = sequences[int(step["order_index"]) - 1]
'''
text = replace_once(text, old, new, "compiler listening story exception")
path.write_text(text, encoding="utf-8")

# 6) Full runtime integrity: recognize item-context stories and audio sequences.
path = Path("services/api/test_full_student_content_integrity.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "from content_runtime import active_options, canonical_id, canonical_interaction, media_gaps, presentation_data, step_assets\n",
    "from content_runtime import active_options, canonical_id, canonical_interaction, item_assets, media_gaps, presentation_data, step_assets\n",
    "integrity item_assets import",
)
old = '''                if interaction in LISTEN:
                    prompt_audio = [asset for asset in audio_assets if asset.get("usage") == "prompt"]
                    if len(prompt_audio) != 1 and not gaps:
                        _issue(errors, canonical, step.order_index, f"listening round prompt-audio count is {len(prompt_audio)}")
'''
new = '''                if interaction in LISTEN:
                    prompt_audio = [asset for asset in audio_assets if asset.get("usage") == "prompt"]
                    round_presentation = presentation_data(item, step)
                    stimulus_contract = round_presentation.get("stimulus") or {}
                    approval = (item.template_data or {}).get("content_approval_2026_09_08") or {}
                    intro = approval.get("context_intro") or {}
                    if intro.get("kind") == "audio_story":
                        if prompt_audio:
                            _issue(errors, canonical, step.order_index, "story audio leaked into a comprehension round")
                        story_audio = [
                            asset for asset in item_assets(item)
                            if asset.get("asset_type") == "audio" and asset.get("usage") == "story_prompt"
                        ]
                        if len(story_audio) != 1:
                            _issue(errors, canonical, None, f"story-context audio count is {len(story_audio)}")
                    elif stimulus_contract.get("kind") == "audio_sequence":
                        targets = [str(value) for value in stimulus_contract.get("audio_targets") or []]
                        actual_targets = [str(asset.get("semantic_text") or "") for asset in prompt_audio]
                        if len(targets) < 2 or actual_targets != targets:
                            _issue(
                                errors,
                                canonical,
                                step.order_index,
                                f"audio-sequence contract mismatch targets={targets} actual={actual_targets}",
                            )
                    elif len(prompt_audio) != 1 and not gaps:
                        _issue(errors, canonical, step.order_index, f"listening round prompt-audio count is {len(prompt_audio)}")
'''
text = replace_once(text, old, new, "integrity listening contract")
path.write_text(text, encoding="utf-8")

# 7) Current PRE-Q05 has four approved image choices.
path = Path("services/api/test_recovery_contracts.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    '    assert {asset["asset_id"] for asset in images} == {"VOC-01", "VOC-02", "VOC-03"}\n',
    '    assert {asset["asset_id"] for asset in images} == {"VOC-01", "VOC-02", "VOC-03", "VOC-04"}\n',
    "PRE-Q05 image pool",
)
path.write_text(text, encoding="utf-8")

# 8) Seed-twice media identity: normalize absent item/step IDs before tuple sorting.
path = Path("services/api/test_seed_all.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    '''                int(link.item_id) if link.item_id is not None else None,
                int(link.step_id) if link.step_id is not None else None,
''',
    '''                int(link.item_id) if link.item_id is not None else 0,
                int(link.step_id) if link.step_id is not None else 0,
''',
    "seed media sort normalization",
)
path.write_text(text, encoding="utf-8")

# 9) Structured-presentation regressions assert current canonical release wording.
path = Path("services/api/test_structured_projection_runtime.py")
text = path.read_text(encoding="utf-8")
text = replace_once(text, '    assert experience.get("projection_contract") == "structured_db_runtime_v1"\n', '    assert experience.get("projection_contract") == "canonical_release_v3"\n', "projection contract")
text = replace_once(text, '        assert evidence["question_text"] == "اختر جملة الدليل المناسبة."\n', '        assert evidence["question_text"] == "اختر الجملة التي تدل على أن الجو ممطر."\n', "evidence question")
text = replace_once(text, '        assert title["question_text"] == "اختر عنوان النص المناسب."\n', '        assert title["question_text"] == "اختر العنوان المناسب للصورة."\n', "title question")
text = replace_once(text, '        assert addition["question_text"] == "اختر معنى الكلمة من الجملة."\n', '        assert addition["question_text"] == "ما معنى كلمة «قُرْبَ»؟"\n', "vocabulary question")
text = replace_once(text, '        assert onset["question_text"] == "استمع إلى الكلمتين، ثم حدّد: هل تبدأان بالصوت نفسه أم بصوتين مختلفين؟"\n', '        assert onset["question_text"] == "هل تبدأ الكلمتان بالصوت نفسه أم بصوتين مختلفين؟"\n', "onset question")
path.write_text(text, encoding="utf-8")

# 10) Student-question regressions consume canonical structured contracts only.
path = Path("services/api/test_student_question_experience.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "from content_runtime import canonical_id, canonical_interaction, instruction_text, presentation_data\n",
    "from content_runtime import canonical_id, canonical_interaction, instruction_text, presentation_data, step_assets\n",
    "student question step_assets import",
)
old = '''        pair = (onset.template_data or {}).get("onset_pair_compare") or {}
        assert [round_data["audio_words"] for round_data in pair.get("rounds", [])] == [
            ["موز", "ماء"],
            ["باب", "بطة"],
            ["قلم", "كرة"],
            ["سمك", "شمس"],
            ["نور", "نخلة"],
        ]
'''
new = '''        steps = sorted(onset.steps, key=lambda value: value.order_index)
        assert [
            [
                str(asset.get("semantic_text") or "")
                for asset in step_assets(onset, step)
                if asset.get("asset_type") == "audio" and asset.get("usage") == "prompt"
            ]
            for step in steps
        ] == [
            ["موز", "ماء"],
            ["باب", "بطة"],
            ["قلم", "كرة"],
            ["سمك", "شمس"],
            ["نور", "نخلة"],
        ]
'''
text = replace_once(text, old, new, "onset runtime source")
old = '''            data = item.template_data or {}
            story = data.get("auditory_story") or {}
            assert story.get("student_visible_story_text") is False
            assert story.get("skill") == "الفهم السمعي المباشر"
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert expected_title in str(data.get("title") or "")
'''
new = '''            data = item.template_data or {}
            assert "auditory_story" not in data
            approval = data.get("content_approval_2026_09_08") or {}
            intro = approval.get("context_intro") or {}
            assert intro.get("kind") == "audio_story"
            assert not str(intro.get("text") or "").strip()
            assert item.skill is not None and item.skill.name == "الفهم السمعي المباشر"
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert expected_title in str(data.get("title") or "")
'''
text = replace_once(text, old, new, "auditory story canonical contract")
path.write_text(text, encoding="utf-8")
