import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import Page from './page';

it('creates a V2 learner and displays the issued code only after a validated response', async()=>{
  const fetcher=jest.fn().mockResolvedValue({ok:true,json:async()=>({source:'himma_v2_account',id:42,access_code:'529374'})});
  global.fetch=fetcher;
  render(<Page/>);
  fireEvent.change(screen.getByLabelText('اسم الطالب'),{target:{value:'طالب اصطناعي'}});
  fireEvent.click(screen.getByRole('button',{name:'إضافة الطالب'}));
  await screen.findByTestId('student-created-state');
  expect(screen.getByTestId('student-access-code')).toHaveTextContent('529374');
  expect(screen.getByRole('link', {name: 'فتح ملف الطالب'})).toHaveAttribute('href','/admin/students/42');
  expect(fetcher).toHaveBeenCalledWith('/api/v2/student/admin/students',expect.objectContaining({method:'POST'}));
});

it('rejects an unverified creation response without displaying a code', async()=>{
  global.fetch=jest.fn().mockResolvedValue({ok:true,json:async()=>({source:'himma_v1_account',access_code:'529374'})});
  render(<Page/>);
  fireEvent.change(screen.getByLabelText('اسم الطالب'),{target:{value:'طالب اصطناعي'}});
  fireEvent.click(screen.getByRole('button',{name:'إضافة الطالب'}));
  await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('تعذر التحقق من حساب هِمّة V2 الجديد.'));
  expect(screen.queryByTestId('student-access-code')).not.toBeInTheDocument();
});

it('does not create duplicate students on two immediate form submissions', async () => {
  let finish!: (value: unknown) => void;
  const pending = new Promise(resolve => { finish = resolve; });
  const fetcher = jest.fn().mockReturnValue(pending);
  global.fetch = fetcher;
  render(<Page />);
  fireEvent.change(screen.getByLabelText('اسم الطالب'), { target: { value: 'طالب اصطناعي' } });
  const form = screen.getByTestId('create-student-form');
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(fetcher).toHaveBeenCalledTimes(1);
  finish({ ok: true, json: async () => ({ source: 'himma_v2_account', id: 42, access_code: '529374' }) });
  expect(await screen.findByTestId('student-created-state')).toBeInTheDocument();
});

it('does not claim a student code was copied when browser clipboard permission fails', async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true, json: async () => ({ source: 'himma_v2_account', id: 42, access_code: '529374' }),
  });
  const original = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: jest.fn().mockRejectedValue(new Error('not allowed')) },
  });
  try {
    render(<Page />);
    fireEvent.change(screen.getByLabelText('اسم الطالب'), { target: { value: 'طالب اصطناعي' } });
    fireEvent.click(screen.getByRole('button', { name: 'إضافة الطالب' }));
    await screen.findByTestId('student-access-code');
    fireEvent.click(screen.getByRole('button', { name: 'نسخ رمز الدخول' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('نسخه يدويًا');
    expect(screen.queryByText('تم نسخ رمز الدخول.')).not.toBeInTheDocument();
    expect(screen.getByTestId('student-access-code')).toHaveTextContent('529374');
  } finally {
    if (original) Object.defineProperty(navigator, 'clipboard', original);
    else Reflect.deleteProperty(navigator, 'clipboard');
  }
});

it('handles an unverified creation response without suggesting an unsafe duplicate submission', async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true, json: async () => ({ source: 'himma_v2_account', id: 42 }),
  });
  render(<Page />);
  fireEvent.change(screen.getByLabelText('اسم الطالب'), { target: { value: 'طالب اصطناعي' } });
  fireEvent.click(screen.getByRole('button', { name: 'إضافة الطالب' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('تحقق من قائمة الطلاب قبل محاولة إضافته');
  expect(screen.queryByTestId('student-created-state')).not.toBeInTheDocument();
});

it.each([
  ["١٢٣٤٥٦", "123456"],
  ["۱۲۳۴۵۶", "123456"],
])("accepts Arabic keyboard numerals in manual access codes: %s", async (entered, expected) => {
  const fetcher=jest.fn().mockResolvedValue({ok:true,json:async()=>({source:"himma_v2_account",id:42,access_code:expected})});
  global.fetch=fetcher;
  render(<Page/>);
  fireEvent.change(screen.getByLabelText("اسم الطالب"), {target:{value:"طالب اصطناعي"}});
  fireEvent.click(screen.getByRole("button",{name:"إدخال يدوي"}));
  fireEvent.change(screen.getByLabelText("اكتب 6 أرقام"), {target:{value:entered}});
  expect(screen.getByLabelText("اكتب 6 أرقام")).toHaveValue(expected);
  fireEvent.click(screen.getByRole("button",{name:"إضافة الطالب"}));
  await screen.findByTestId("student-created-state");
  const call = (fetcher.mock.calls as unknown as Array<[string, { body: string }]>)[0];
  expect(JSON.parse(call[1].body).access_code).toBe(expected);
});
