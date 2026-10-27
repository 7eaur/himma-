import {execFileSync} from 'child_process';
import path from 'path';
import {mkdir} from 'fs/promises';
import {test,expect} from '@playwright/test';

const API=process.env.NEXT_PUBLIC_API_URL??'http://localhost:8000';
const PASSWORD=process.env.E2E_RESEARCHER_PASSWORD;
const USERNAME=process.env.E2E_RESEARCHER_USERNAME??'admin';

test('W4 real V2 ledger reconciliation is idempotent and identical on Student and Admin refresh',async({page,context,request})=>{
  test.setTimeout(150000);
  if(!PASSWORD)throw new Error('E2E_RESEARCHER_PASSWORD required');
  const root=path.resolve(__dirname,'../../../../services/api');
  const output=execFileSync('python',[path.join(root,'tests/support/v2_reward_fixture.py')],{cwd:root,env:process.env,encoding:'utf8'}).trim();
  const fixture=JSON.parse(output.split(/\r?\n/).at(-1)??'{}') as {student_id:number;name:string;access_code:string};
  async function login(student:boolean){
    await context.clearCookies();
    const response=await request.post(`${API}/auth/${student?'student-login':'login'}`,{data:student?{access_code:fixture.access_code}:{username:USERNAME,password:PASSWORD}});
    expect(response.status()).toBe(200);
    const token=response.headers()['set-cookie']?.match(/access_token=([^;]+)/)?.[1];
    expect(token).toBeTruthy();
    await context.addCookies([{name:'access_token',value:token!,domain:'localhost',path:'/',httpOnly:true,secure:false,sameSite:'Lax'}]);
  }
  await login(true);
  const before=await request.get(`${API}/v2/student/home`);
  expect((await before.json()).rewards.total_stars).toBe(0); // GET never grants.
  await login(false);
  await page.goto(`/admin/students/${fixture.student_id}`);
  await expect(page.getByTestId('v2-star-total')).toHaveText('0 نجمة');
  await page.getByRole('button',{name:'مزامنة الاستحقاقات المثبتة'}).click();
  await expect(page.getByTestId('v2-star-total')).toHaveText('3 نجمة');
  await page.getByRole('button',{name:'مزامنة الاستحقاقات المثبتة'}).click();
  await expect(page.getByText('تم التحقق من الاستحقاقات. منح جديدة: 0.')).toBeVisible();
  await page.reload();
  await expect(page.getByTestId('v2-star-total')).toHaveText('3 نجمة');
  const staff=await request.get(`${API}/v2/student/admin/students/${fixture.student_id}/home`);
  const staffRewards=(await staff.json()).rewards;
  expect(staffRewards.source).toBe('himma_v2_reward_ledger');
  expect(staffRewards.lessons).toHaveLength(1);
  expect(staffRewards.badges).toHaveLength(0);
  await login(true);
  await page.setViewportSize({width:390,height:844});
  await page.goto('/student');
  await expect(page.getByTestId('v2-star-total')).toHaveText('3 نجمة');
  await page.reload();
  await expect(page.getByTestId('v2-star-total')).toHaveText('3 نجمة');
  const child=await request.get(`${API}/v2/student/home`);
  expect((await child.json()).rewards).toEqual(staffRewards);
  await mkdir('playwright-report/screenshots',{recursive:true});
  await page.screenshot({path:'playwright-report/screenshots/w4-v2-earned-stars-synthetic.png',fullPage:true});
});
