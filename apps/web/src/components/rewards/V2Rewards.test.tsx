import {fireEvent,render,screen} from '@testing-library/react';
import V2Rewards, {type V2RewardsData} from './V2Rewards';
const data:V2RewardsData={state:'ready',source:'himma_v2_reward_ledger',policy_version:'himma-v2-effort/1',total_stars:3,badges:[],lessons:[{lesson_id:'L1-01',title:'الحرف وصوته',stars:3,milestones:[{key:'intro_video',label:'أكملت التمهيد والفيديو'},{key:'guided_practice',label:'أكملت التدريب'},{key:'lesson_complete',label:'أكملت الدرس'}]}]};
it('renders the same ledger total and earned badge for learner and supervisor',()=>{
 const earned={...data,badges:[{id:1,key:'v2:L1:learned',label:'مستكشف الحروف',asset_path:'/assets/rewards/svg/hem-bdg-04-letter-explorer.svg'}]};
 const {rerender}=render(<V2Rewards data={earned}/>);
 expect(screen.getByTestId('v2-star-total')).toHaveTextContent('3 نجمة');
 expect(screen.getByRole('img',{name:'شارة مستكشف الحروف'})).toBeVisible();
 expect(screen.getByTestId('canonical-reward-badge')).toHaveAttribute('data-reward-key','v2:L1:learned');
 rerender(<V2Rewards data={earned} variant='admin'/>);
 expect(screen.getByTestId('v2-star-total')).toHaveTextContent('3 نجمة');
});
it('does not invent a badge for an empty ledger or display a second points currency',()=>{
 render(<V2Rewards data={{...data,total_stars:0,badges:[],lessons:[]}}/>);
 expect(screen.getByTestId('v2-star-total')).toHaveTextContent('0 نجمة');
 expect(screen.queryByTestId('canonical-reward-badge')).not.toBeInTheDocument();
 expect(screen.queryByText(/نقاط|ترتيب/)).not.toBeInTheDocument();
});
it('shows earned milestone explanations without exposing lesson identifiers',()=>{
 render(<V2Rewards data={data}/>);
 fireEvent.click(screen.getByText('خطواتي المكتملة'));
 expect(screen.getByText('أكملت التدريب')).toBeInTheDocument();
 expect(screen.queryByText('L1-01')).not.toBeInTheDocument();
});
