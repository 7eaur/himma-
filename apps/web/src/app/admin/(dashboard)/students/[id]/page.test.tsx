import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import Page from './page';
let currentId = '1';
jest.mock('next/navigation',()=>({useParams:()=>({id:currentId})}));
const home = (id:number) => ({mode:'v2',test_only:true,student:{id,full_name:`طالب اصطناعي ${id}`,grade_level:3},journey:null,current_action:{action:'start_pretest',label:'ابدأ الاختبار القبلي',href:null},progress:{completed_lessons:0,assigned_lessons:null,skipped_by_placement:0,pending_review:0,display_percent:null},assessments:{pretest:null,posttest:null},rewards:{state:'ready',source:'himma_v2_reward_ledger',policy_version:'himma-v2-effort/1',total_stars:0,badges:[],lessons:[]},data_status:'ready',lesson_overview:{state:'awaiting_journey',items:[],content_release_version:null}});
const account=(id:number)=>({source:'himma_v2_account',id,full_name:`طالب اصطناعي ${id}`,grade_level:3,status:'active',created_at:'2026-10-27T00:00:00Z',posttest_enabled:false});
function setup(){
 currentId='1';
 window.history.replaceState({}, '', '/admin/students/1');
 const fetcher=jest.fn().mockImplementation((url:string)=>{
  const id=Number(url.match(/students\/(\d+)/)?.[1]||1);
  const data=url.endsWith('/home')? home(id):url.endsWith('/reveal')? {student_id:id,access_code:'123456'}:account(id);
  return Promise.resolve({ok:true,json:async()=>data});
 });
 global.fetch=fetcher;return fetcher;
}
it('loads identity and V2 data without requesting V1 or learner credentials',async()=>{
 const fetcher=setup();render(<Page/>);
 await screen.findByRole('heading',{name:'طالب اصطناعي 1'});
 await screen.findByTestId('supervisor-v2-overview');
 expect(fetcher.mock.calls.map(([url])=>url).sort()).toEqual(['/api/v2/student/admin/students/1/account','/api/v2/student/admin/students/1/home'].sort());
 expect(screen.queryByText('123456')).not.toBeInTheDocument();
 expect(screen.queryByRole('button',{name:'أرشيف V1 التاريخي'})).not.toBeInTheDocument();
 fireEvent.click(screen.getByRole('tab',{name:'التسجيلات'}));
 expect(screen.getByRole('link',{name:'مراجعة قراءات الدروس'})).toHaveAttribute('href','/admin/v2-lesson-review');
});
it('only fetches a credential after explicit reveal and clears it when leaving account',async()=>{
 const fetcher=setup();render(<Page/>);
 await screen.findByRole('heading',{name:'طالب اصطناعي 1'});
 fireEvent.click(screen.getByRole('tab',{name:'الحساب'}));
 expect(fetcher.mock.calls.some(([url])=>url.includes('/reveal'))).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'إظهار الرمز'}));
 expect(await screen.findByText('123456')).toBeVisible();
 expect(fetcher).toHaveBeenCalledWith('/api/v2/student/admin/students/1/access-code/reveal',expect.objectContaining({method:'POST'}));
 fireEvent.click(screen.getByRole('tab',{name:'نظرة عامة'}));
 fireEvent.click(screen.getByRole('tab',{name:'الحساب'}));
 expect(screen.queryByText('123456')).not.toBeInTheDocument();
});
it('never reveals a code when the explicit request fails',async()=>{
 const fetcher=setup();fetcher.mockImplementation((url:string)=>Promise.resolve({ok:!url.endsWith('/reveal'),json:async()=>url.endsWith('/home')?home(1):account(1)}));
 render(<Page/>);await screen.findByRole('heading',{name:'طالب اصطناعي 1'});
 fireEvent.click(screen.getByRole('tab',{name:'الحساب'}));
 fireEvent.click(screen.getByRole('button',{name:'إظهار الرمز'}));
 await screen.findByText('تعذر إظهار رمز الدخول.');
 expect(screen.queryByText('123456')).not.toBeInTheDocument();
});
it('remounts identity state when routing to another learner',async()=>{
 const fetcher=setup();const {rerender}=render(<Page/>);
 await screen.findByRole('heading',{name:'طالب اصطناعي 1'});
 fireEvent.click(screen.getByRole('tab',{name:'الحساب'}));
 fireEvent.click(screen.getByRole('button',{name:'إظهار الرمز'}));await screen.findByText('123456');
 currentId='2';rerender(<Page/>);
 await screen.findByRole('heading',{name:'طالب اصطناعي 2'});
 expect(screen.queryByText('123456')).not.toBeInTheDocument();
 expect(screen.getByTestId('supervisor-v2-overview')).toBeVisible();
 await waitFor(()=>expect(fetcher).toHaveBeenCalledWith('/api/v2/student/admin/students/2/account',expect.anything()));
});
it('shows seven task-specific sections without rendering the long lesson list on overview',async()=>{
 setup();render(<Page/>);
 await screen.findByRole('heading',{name:'طالب اصطناعي 1'});
 expect(screen.getAllByRole('tab')).toHaveLength(7);
 expect(screen.queryByTestId('supervisor-lesson-disclosure')).not.toBeInTheDocument();
 fireEvent.click(screen.getByRole('tab',{name:'المسار والدروس'}));
 expect(screen.getByTestId('supervisor-lesson-disclosure')).toHaveAttribute('open');
 expect(screen.getByText('تفاصيل الدروس (0)')).toBeInTheDocument();
 expect(screen.queryByText(/أرشيف|التاريخي|V1/)).not.toBeInTheDocument();
});
