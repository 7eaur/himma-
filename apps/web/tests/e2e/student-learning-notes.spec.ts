import { expect, test } from "@playwright/test";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DIR = path.join(process.cwd(), "playwright-report/screenshots/student-learning-notes");
const viewports = [320, 360, 390, 430, 768, 1440];

test("student map, placed levels and delayed educational images retain clear mobile states", async ({ page, request, context }) => {
  test.setTimeout(180000);
  await mkdir(DIR, { recursive: true });
  const password = process.env.E2E_RESEARCHER_PASSWORD;
  if (!password) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  expect((await request.post(`${API}/auth/login`, {data:{username:process.env.E2E_RESEARCHER_USERNAME ?? "admin",password}})).status()).toBe(200);
  const created = await request.post(`${API}/researcher/students`, {data:{full_name:`مراجعة مسار الهاتف ${Date.now()}`,grade_level:3}});
  expect(created.status()).toBe(201);
  const student = await request.post(`${API}/auth/student-login`, {data:{access_code:(await created.json()).access_code}});
  expect(student.status()).toBe(200);
  const cookie = student.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{name:"access_token",value:cookie!,domain:"localhost",path:"/",httpOnly:true,sameSite:"Lax",secure:false}]);
  await page.route(/\/api\/v2\/retries\/student\/tasks(?:\?.*)?$/, route => route.fulfill({json:{items:[]}}));

  const authored = (await Promise.all([1,2,3].map(async level => {
    const bank = JSON.parse(await readFile(path.resolve(process.cwd(), `../../docs/v2/content-bank/L${level}_AUTHORING_BANK_DRAFT.json`), "utf8"));
    return bank.lessons.map((lesson: {id:string;title:string;level:string}) => ({lesson_id:lesson.id,title:lesson.title,level:lesson.level}));
  }))).flat() as {lesson_id:string;title:string;level:string}[];
  let placedLevel = 1;
  await page.route("**/api/v2/lessons/catalog", route => route.fulfill({json:{lessons:authored.map(lesson => {
    const level = Number(lesson.level.slice(1));
    const index = Number(lesson.lesson_id.split("-")[1]);
    const state = level < placedLevel ? "skipped" : level === placedLevel && index === 1 ? "done" : level === placedLevel && index === 2 ? "current" : "locked";
    return {...lesson,state,preview_enabled:state === "current",session_id:state === "current" ? 44 : null};
  })}}));
  await page.route("**/api/v2/student/home", route => route.fulfill({json:{
    mode:"v2",student:{id:777,full_name:"طالب المسار",grade_level:3},data_status:"ready",
    journey:{current_level:placedLevel,placement_state:"placed",current_lesson_id:`L${placedLevel}-02`,content_release_version:"visual-fixture"},
    current_action:{action:"lesson_catalog",href:"/student/learning-v2",label:"متابعة دروسي"},
    progress:{completed_lessons:1,assigned_lessons:19-(placedLevel-1)*6,skipped_by_placement:(placedLevel-1)*6,pending_review:0,display_percent:8},
    assessments:{pretest:{official:true,state:"completed",session_id:1,score_percent:placedLevel===1?30:placedLevel===2?65:90},posttest:null},
    levels:[1,2,3].map(level=>({level,state:level<placedLevel?"skipped":level===placedLevel?"current":"locked",assigned_lessons:level<placedLevel?0:level===3?7:6,completed_lessons:level===placedLevel?1:0,display_percent:level<placedLevel?null:0})),
    rewards:{state:"ready",source:"himma_v2_reward_ledger",policy_version:"visual-fixture",total_stars:3,badges:[],lessons:[]},
  }}));

  for (placedLevel of [1,2,3]) {
    for (const width of viewports) {
      await page.setViewportSize({width,height:width>=768?1000:844});
      await page.goto("/student/learning-v2");
      const currentLevel = page.locator(`details[data-level="L${placedLevel}"]`);
      await expect(currentLevel).toHaveAttribute("open", "");
      await expect(page.getByRole("button",{name:"متابعة الدرس",exact:true})).toBeVisible();
      await expect(currentLevel.locator('[data-lesson-state="done"]')).toHaveCount(1);
      for (let lower = 1; lower < placedLevel; lower++) {
        const previous = page.locator(`details[data-level="L${lower}"]`);
        await expect(previous).not.toHaveAttribute("open", "");
        await expect(previous.locator("summary")).toContainText("بدأت من مستوى أعلى");
      }
      await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      await page.screenshot({path:path.join(DIR,`map-L${placedLevel}-${width}.png`),fullPage:true});
      await page.goto("/student");
      await expect(page.getByRole("region",{name:"مستويات رحلتي"})).toBeVisible();
      await expect(page.getByRole("link",{name:"عرض إنجازاتي"})).toBeVisible();
      await expect(page.locator('[data-level-state="skipped"]')).toHaveCount(placedLevel-1);
      await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      await page.screenshot({path:path.join(DIR,`dashboard-L${placedLevel}-${width}.png`),fullPage:true});
    }
  }

  await page.setViewportSize({width:390,height:844});
  let releaseImage: (()=>void) | undefined;
  const imageWait = new Promise<void>(resolve=>{releaseImage=resolve;});
  const imageBytes = await readFile(path.resolve(process.cwd(),"../../assets/education/assets/vocabulary/webp/hem-voc-06-sun-512.webp"));
  await page.route("**/api/visual-test-image.webp", async route=>{await imageWait;await route.fulfill({contentType:"image/webp",body:imageBytes});});
  await page.route("**/api/v2/assessments/sessions/777", route=>route.fulfill({json:{
    session:{session_id:777,kind:"pretest",state:"answering",progress:{answered:11,total:30}},
    interaction:{question:{question_id:"V2-PRE-Q12",role:"pretest",interaction:"build_word",prompt:"انظر إلى الصورة، ثم رتّب الحروف لتكوّن اسمها.",stimulus:{text:null,media:[{media_id:"VOC-06",kind:"image"}]},options:[{id:"a",text:"س",media:[]},{id:"b",text:"ش",media:[]},{id:"c",text:"م",media:[]}]},media:{"VOC-06":{asset_id:"VOC-06",kind:"image",state:"ready",url:"/api/visual-test-image.webp",test_only:false}},progress:{index:12,total:30,stage:"pretest"},attempts:0},summary:{pending_review:0},
  }}));
  await page.goto("/student/assessment-v2/777",{waitUntil:"domcontentloaded"});
  await expect(page.getByRole("status",{name:"جاري تحميل الصورة"})).toBeVisible();
  for (const index of [2,3,1]) await page.getByRole("button",{name:`اختيار الخيار ${index}`}).click();
  await expect(page.getByRole("button",{name:"حفظ الإجابة والمتابعة"})).toBeDisabled();
  await page.screenshot({path:path.join(DIR,"image-wait-390.png"),fullPage:true});
  releaseImage?.();
  await expect(page.getByRole("status",{name:"جاري تحميل الصورة"})).toHaveCount(0);
  await expect(page.getByRole("button",{name:"حفظ الإجابة والمتابعة"})).toBeEnabled();
  await page.screenshot({path:path.join(DIR,"image-ready-390.png"),fullPage:true});
});
