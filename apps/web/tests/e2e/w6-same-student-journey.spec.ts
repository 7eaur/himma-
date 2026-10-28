import {expect, test, type APIRequestContext, type BrowserContext} from '@playwright/test';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? 'admin';
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function addCookie(context: BrowserContext, response: Awaited<ReturnType<APIRequestContext['post']>>) {
  const code = response.headers()['set-cookie']?.match(/access_token=([^;]+)/)?.[1];
  expect(code).toBeTruthy();
  await context.addCookies([{name:'access_token',value:code!,domain:'localhost',path:'/',httpOnly:true,sameSite:'Lax',secure:false}]);
}

test('W6: one new identity begins V2 pretest and uses its V2 account record', async ({page,context,request})=>{
  if (!PASSWORD) throw new Error('E2E_RESEARCHER_PASSWORD required');
  const admin=await request.post(`${API_URL}/auth/login`,{data:{username:USERNAME,password:PASSWORD}});
  expect(admin.status()).toBe(200);
  await addCookie(context,admin);
  await page.goto('/admin/students/new');
  const name=`طالب رحلة W6 ${Date.now()}`;
  await page.getByTestId('input-student-name').fill(name);
  await page.getByTestId('submit-create-student').click();
  await expect(page.getByTestId('student-access-code')).toBeVisible();
  const code=(await page.getByTestId('student-access-code').innerText()).trim();
  expect(code).toMatch(/^\d{6}$/);
  const rows=await request.get(`${API_URL}/researcher/students`);
  expect(rows.status()).toBe(200);
  const student=(await rows.json() as Array<{id:number;access_code:string;full_name:string}>).find(row=>row.access_code===code);
  expect(student?.full_name).toBe(name);
  await page.goto(`/admin/students/${student!.id}`);
  await expect(page.getByTestId('supervisor-v2-action')).toContainText('ابدأ الاختبار القبلي');
  await expect(page.getByRole('button',{name:'أرشيف V1 التاريخي'})).toHaveCount(0);

  await context.clearCookies();
  const learner=await request.post(`${API_URL}/auth/student-login`,{data:{access_code:code}});
  expect(learner.status()).toBe(200);
  await addCookie(context,learner);
  await page.goto('/student');
  await expect(page.getByTestId('student-home')).toHaveAttribute('data-learning-version','v2');
  await page.getByTestId('student-primary-action').click();
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  await expect(page.getByTestId('v2-interaction-player')).toContainText('1 من 30');
  await page.goto('/student');
  await expect(page.getByTestId('student-primary-action')).toHaveText('متابعة الاختبار');

  await context.clearCookies();
  await addCookie(context,admin);
  const adminAgain=await request.post(`${API_URL}/auth/login`,{data:{username:USERNAME,password:PASSWORD}});
  expect(adminAgain.status()).toBe(200);
  const account=await request.get(`${API_URL}/v2/student/admin/students/${student!.id}/account`);
  expect(account.status()).toBe(200);
  expect((await account.json()).id).toBe(student!.id);
  await page.goto(`/admin/students/${student!.id}`);
  await expect(page.getByRole('heading',{name})).toBeVisible();
  await expect(page.getByTestId('supervisor-v2-action')).toContainText('متابعة الاختبار');
});
