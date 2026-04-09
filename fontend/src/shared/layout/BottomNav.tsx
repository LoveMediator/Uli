import { CalendarDays, HeartHandshake, Home, User2 } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/shared/lib';

const items = [
  { to: '/app/home', label: '主页', icon: Home },
  { to: '/app/mediation', label: '调解', icon: HeartHandshake },
  { to: '/app/calendar', label: '日历', icon: CalendarDays },
  { to: '/app/profile', label: '我的', icon: User2 },
];

export function BottomNav() {
  return (
    <nav className="glass-nav absolute inset-x-0 bottom-0 z-30 rounded-b-[34px] px-6 pb-6 pt-3">
      <div className="flex items-center justify-between">
        {items.map((item) => (
          <NavLink key={item.to} to={item.to} className="w-16">
            {({ isActive }) => {
              const Icon = item.icon;
              return (
                <div className="group flex flex-col items-center justify-center">
                  <div
                    className={cn(
                      'rounded-2xl p-2 transition duration-300',
                      isActive ? 'bg-milk-100 shadow-sm' : 'group-hover:bg-milk-100/80',
                    )}
                  >
                    <Icon
                      className={cn(
                        'h-6 w-6 text-coffee-800 transition-transform group-hover:-translate-y-1',
                        isActive && '-translate-y-1',
                      )}
                    />
                  </div>
                  <span
                    className={cn(
                      'mt-0.5 text-[10px] font-bold',
                      isActive ? 'text-coffee-900' : 'text-coffee-800/50',
                    )}
                  >
                    {item.label}
                  </span>
                </div>
              );
            }}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
