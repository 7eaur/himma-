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
