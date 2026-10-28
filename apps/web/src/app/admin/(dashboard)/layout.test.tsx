import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import AdminDashboardLayout from './layout';

const mockReplace = jest.fn();
const mockRefresh = jest.fn();
jest.mock('next/navigation', () => ({
  usePathname: () => '/admin/students/12',
  useRouter: () => ({replace: mockReplace, refresh: mockRefresh}),
}));
jest.mock('@/components/admin/AdminNotifications', () => function MockNotifications() {return <span>إشعارات V2</span>;});
jest.mock('@/hooks/useAccessibleDialog', () => ({useAccessibleDialog: () => undefined}));

it('shows V2 review navigation without mounting old reinforcement or archive requests', async () => {
  const fetcher=jest.fn().mockResolvedValue({ok:true,json:async()=>({role:'researcher',display_name:'مشرف اختبار'})});
  global.fetch=fetcher;
  render(<AdminDashboardLayout><div>محتوى الطالب</div></AdminDashboardLayout>);
  expect(await screen.findByText('محتوى الطالب')).toBeVisible();
  expect(screen.getByRole('link',{name:'مركز مراجعة التسجيلات'})).toHaveAttribute('href','/admin/v2-review-center');
  expect(screen.getByRole('link',{name:'بنك الدروس والأسئلة'})).toHaveAttribute('href','/admin/content-preview');
  expect(screen.getByText('مراجعة الصوت')).toBeInTheDocument();
  expect(screen.queryByText('أرشيف V1 التاريخي')).not.toBeInTheDocument();
  expect(screen.queryByText('تسجيلات النسخة السابقة')).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalled();
  expect(fetcher.mock.calls.every(([url])=>url==='/api/auth/me')).toBe(true);
});

it('does not falsely confirm supervisor logout when the server fails', async () => {
  mockReplace.mockClear();
  const fetcher=jest.fn().mockImplementation((url:string) => url === '/api/auth/me'
    ? Promise.resolve({ok:true,json:async()=>({role:'researcher',display_name:'مشرف اختبار'})})
    : Promise.resolve({ok:false,status:503}));
  global.fetch=fetcher;
  render(<AdminDashboardLayout><div>محتوى محمي</div></AdminDashboardLayout>);
  await screen.findByText('محتوى محمي');
  fireEvent.click(screen.getByRole('button', {name:'تسجيل الخروج'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('تعذر تأكيد تسجيل الخروج');
  expect(mockReplace).not.toHaveBeenCalled();
  expect(screen.getByRole('button',{name:'إعادة محاولة الخروج'})).toBeEnabled();
  expect(fetcher).toHaveBeenCalledWith('/api/auth/logout',{method:'POST'});
});

it('navigates away only after logout is acknowledged', async () => {
  mockReplace.mockClear();
  mockRefresh.mockClear();
  global.fetch=jest.fn().mockImplementation((url:string) => Promise.resolve({
    ok:true,json:async()=> url === '/api/auth/me'
      ? {role:'researcher',display_name:'مشرف اختبار'} : {},
  }));
  render(<AdminDashboardLayout><div>محتوى محمي</div></AdminDashboardLayout>);
  await screen.findByText('محتوى محمي');
  fireEvent.click(screen.getByRole('button',{name:'تسجيل الخروج'}));
  await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/admin/login'));
  expect(mockRefresh).toHaveBeenCalled();
});
