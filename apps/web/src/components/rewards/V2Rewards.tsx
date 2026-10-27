import { Star } from 'lucide-react';
import CanonicalRewardBadge from './CanonicalRewardBadge';

export interface V2RewardsData {
  state: 'ready'; source: 'himma_v2_reward_ledger'; policy_version: string; release_id?: number | null;
  total_stars: number;
  badges: {id:number;key:string;label:string;asset_path:string}[];
  lessons: {lesson_id:string;title:string;stars:number;milestones:{key:string;label:string}[]}[];
}
export default function V2Rewards({data,variant='student'}:{data:V2RewardsData;variant?:'student'|'admin'}) {
  const valid=data?.source==='himma_v2_reward_ledger' && data.state==='ready' && Number.isSafeInteger(data.total_stars) && data.total_stars>=0 && Array.isArray(data.badges) && Array.isArray(data.lessons);
  return <section aria-label={variant==='admin'?'مكافآت تعلم V2':'نجومي وإنجازاتي'} className="mt-5 min-w-0 rounded-3xl border border-border bg-white p-5" data-testid="v2-rewards">
    <h2 className="mb-3 text-lg font-bold text-navy">{variant==='admin'?'مكافآت تعلم V2':'نجومي وإنجازاتي'}</h2>
    {!valid ? <p role="status">تعذر تحميل الإنجازات الآن. حاول مجددًا بعد قليل.</p> : <>
      <p className="flex items-center gap-3 text-lg font-bold text-navy"><Star aria-hidden="true" className="text-amber-600"/><span data-testid="v2-star-total">{data.total_stars} نجمة</span></p>
      <p className="mt-2 text-sm text-muted">{data.total_stars===0?'ستجمع نجومك مع خطوات الدروس. خذ وقتك، وكل خطوة مهمة.':'هذه نجوم الخطوات التي أكملتها. واصل رحلتك على مهلك.'}</p>
      {data.badges.length>0 && <div className="mt-4 grid gap-3 sm:grid-cols-3">{data.badges.map(badge=><CanonicalRewardBadge key={badge.key} label={badge.label} assetPath={badge.asset_path} rewardKey={badge.key} variant={variant}/>)}</div>}
      {data.lessons.length>0 && <details className="mt-4 rounded-2xl bg-slate-50 p-3"><summary className="min-h-11 cursor-pointer font-semibold">خطواتي المكتملة</summary><ul className="mt-3 space-y-3">{data.lessons.map(lesson=><li key={lesson.lesson_id}><strong>{lesson.title} · {lesson.stars} نجمة</strong><ul className="mt-1 space-y-1 text-sm text-muted">{lesson.milestones.map(item=><li key={item.key}>{item.label}</li>)}</ul></li>)}</ul></details>}
    </>}
  </section>;
}
