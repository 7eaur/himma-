import json
import os
import sys
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import SQLALCHEMY_DATABASE_URL
from db.models import Skill, ContentItem, ContentStep, ContentKind, ScoringPolicy, ScoringRule

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'packages', 'content', 'src', 'catalog.json')

def run_seed():
    if not os.path.exists(CATALOG_PATH):
        print(f"Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    db: Session = SessionLocal()
    db_items = {}
    try:
        print(f"Starting seed of {len(catalog)} items...")
        
        # 1. Seed Skills
        skills_created = 0
        processed_skill_keys = set()
        for item in catalog:
            skill_key = item['skill_key']
            skill_name = item['skill_name']
            
            if skill_key in processed_skill_keys:
                continue
                
            existing_skill = db.query(Skill).filter(Skill.skill_key == skill_key).first()
            if not existing_skill:
                new_skill = Skill(
                    skill_key=skill_key,
                    name=skill_name,
                    description=skill_name,
                    level_id=1 # Default
                )
                db.add(new_skill)
                skills_created += 1
            processed_skill_keys.add(skill_key)
        db.commit()
        print(f"Created {skills_created} new skills.")
        
        # Build map for fast lookup
        skills_map = {s.skill_key: s.id for s in db.query(Skill).all()}
        
        # 2. Seed Items
        items_created = 0
        for item in catalog:
            stable_key = item['stable_key']
            kind_str = item['kind']
            if kind_str == 'question':
                kind_str = 'pretest_question'
                
            existing_item = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
            if not existing_item:
                new_item = ContentItem(
                    stable_key=stable_key,
                    kind=ContentKind(kind_str),
                    level_id=1,
                    skill_id=skills_map[item['skill_key']],
                    interaction_type='multiple_choice', # Default placeholder
                    order_index=1,
                    version=item['version'],
                    status=item['status'],
                    checksum='pending_checksum',
                    template_data={}
                )
                db.add(new_item)
                db.flush() # To get new_item.id
                
                # Add steps
                for step_data in item.get('steps', []):
                    new_step = ContentStep(
                        item_id=new_item.id,
                        order_index=step_data['order_index'],
                        prompt_text=step_data['prompt_text'],
                        expected_reading_text=step_data['expected_reading_text']
                    )
                    db.add(new_step)
                
                db_items[stable_key] = new_item
                items_created += 1
        db.commit()
        print(f"Created {items_created} new content items.")

        # 3. Seed Scoring Policy
        policy_version = "SCORING_POLICY_V1"
        policy = db.query(ScoringPolicy).filter(ScoringPolicy.version == policy_version).first()
        if not policy:
            policy = ScoringPolicy(
                version=policy_version,
                status="approved",
                approved_by=None,
                approved_at=datetime.datetime.strptime("2026-08-11", "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc),
                checksum="seeded_by_script"
            )
            db.add(policy)
            db.flush()
            
            for stable_key, db_item in db_items.items():
                if db_item.kind in [ContentKind.pretest_question, ContentKind.posttest_question]:
                    rule = ScoringRule(
                        policy_id=policy.id,
                        item_id=db_item.id,
                        max_raw_score=1.0,
                        rubric="V1: 1 point for correct non-audio. For audio: max(0, 1 - (errors/target_units))"
                    )
                    db.add(rule)
            db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
