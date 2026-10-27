import {expect,test,type APIRequestContext,type BrowserContext} from '@playwright/test';

const API_URL=process.env.NEXT_PUBLIC_API_URL??'http://localhost:8000';
const USERNAME=process.env.E2E_RESEARCHER_USERNAME??'admin';
const PASSWORD=process.env.E2E_RESEARCHER_PASSWORD;

async function cookie(context:BrowserContext,response:Awaited<ReturnType<APIRequestContext['post']>>){
  const value=response.headers()['set-cookie']?.match(/access_token=([^;]+)/)?.[1];
  expect(value).toBeTruthy();
  await context.addCookies([{name:'access_token',value:value!,domain:'localhost',path:'/',httpOnly:true,sameSite:'Lax',secure:false}]);
}

test('public to V2 supervisor to new learner pretest preserves the same identity',async({page,context,request},testInfo)=>{
  if(!PASSWORD)throw new Error('E2E_RESEARCHER_PASSWORD required');
  await page.goto('/');
  await expect(page.getByRole('heading',{name:/اقرأ بثقة/})).toBeVisible();
  await page.goto('/admin');
  await expect(page).toHaveURL(/\/admin\/login/);
  const admin=await request.post(`${API_URL}/auth/login`,{data:{username:USERNAME,password:PASSWORD}});
  expect(admin.status()).toBe(200);
  await cookie(context,admin);
  await page.goto('/admin/students/new');
  const name=`طالب شريحة V2 ${Date.now()}`;
  await page.getByTestId('input-student-name').fill(name);
  await page.getByTestId('submit-create-student').click();
  await expect(page.getByTestId('student-created-state')).toBeVisible();
  const code=(await page.getByTestId('student-access-code').innerText()).trim();
  expect(code).toMatch(/^\d{6}$/);
  const list=await request.get(`${API_URL}/researcher/students`);
  expect(list.status()).toBe(200);
  const student=(await list.json() as Array<{id:number;access_code:string}>).find(row=>row.access_code===code);
  expect(student?.id).toBeTruthy();
  await page.goto(`/admin/students/${student!.id}`);
  await expect(page.getByRole('heading',{name})).toBeVisible();
  await expect(page.getByTestId('supervisor-v2-action')).toContainText('ابدأ الاختبار القبلي');
  await page.screenshot({path:testInfo.outputPath('supervisor-v2-before-pretest.png'),fullPage:true});
  await context.clearCookies();
  const learner=await request.post(`${API_URL}/auth/student-login`,{data:{access_code:code}});
  expect(learner.status()).toBe(200);
  await cookie(context,learner);
  await page.goto('/student');
  await expect(page.getByTestId('student-home')).toHaveAttribute('data-learning-version','v2');
  await page.getByTestId('student-primary-action').click();
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  await expect(page.getByTestId('v2-interaction-player')).toContainText('1 من 30');
  await page.screenshot({path:testInfo.outputPath('student-v2-pretest.png'),fullPage:true});
});
