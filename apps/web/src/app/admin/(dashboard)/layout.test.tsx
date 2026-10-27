import {render, screen} from '@testing-library/react';
import AdminDashboardLayout from './layout';

jest.mock('next/navigation', () => ({
  usePathname: () => '/admin/students/12',
  useRouter: () => ({replace: jest.fn(), refresh: jest.fn()}),
}));
jest.mock('@/components/admin/AdminNotifications', () => function MockNotifications() {return <span>إشعارات V2</span>;});
jest.mock('@/hooks/useAccessibleDialog', () => ({useAccessibleDialog: () => undefined}));

it('shows V2 review navigation without mounting old reinforcement or archive requests', async () => {
  const fetcher=jest.fn().mockResolvedValue({ok:true,json:async()=>({role:'researcher',display_name:'مشرف اختبار'})});
  global.fetch=fetcher;
  render(<AdminDashboardLayout><div>محتوى الطالب</div></AdminDashboardLayout>);
  expect(await screen.findByText('محتوى الطالب')).toBeVisible();
  expect(screen.getByRole('link',{name:'مراجعة دروس V2'})).toHaveAttribute('href','/admin/v2-lesson-review');
  expect(screen.queryByText('أرشيف V1 التاريخي')).not.toBeInTheDocument();
  expect(screen.queryByText('تسجيلات النسخة السابقة')).not.toBeInTheDocument();
  expect(fetcher).toHaveBeenCalled();
  expect(fetcher.mock.calls.every(([url])=>url==='/api/auth/me')).toBe(true);
});
