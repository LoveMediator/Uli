import { Heart, LogOut, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/domains/auth';
import { useCurrentEvent } from '@/domains/mediation';
import { formatEventStatus } from '@/shared/lib';
import { Button, Card } from '@/shared/ui';

export function ProfilePage() {
  const navigate = useNavigate();
  const { usernameDraft, publicId, logout, isLoggingOut } = useAuth();
  const { relationshipId, currentEvent } = useCurrentEvent();
  const currentStatusLabel = formatEventStatus(currentEvent?.status);
  const relationshipLabel = relationshipId || '未绑定';

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-milk-50 pb-32">
      <div className="relative overflow-hidden rounded-b-[40px] bg-milk-200 px-6 pb-10 pt-16">
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/20 blur-2xl" />
        <div className="relative z-10 flex items-center gap-4">
          <div className="relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-white bg-gradient-to-br from-accent-pink to-accent-blue text-2xl font-bold text-white shadow-md">
            {(usernameDraft || 'A').slice(0, 1).toUpperCase()}
            <div className="absolute -bottom-1 -right-1 rounded-full bg-white p-1">
              <Heart className="h-3 w-3 fill-current text-red-400" />
            </div>
          </div>
          <div>
            <h2 className="text-xl font-bold text-coffee-900">{usernameDraft || '未命名用户'}</h2>
            <p className="text-xs font-medium text-coffee-800/60">当前绑定关系：{relationshipLabel}</p>
          </div>
          <button type="button" className="ml-auto rounded-full bg-white/50 p-2 transition hover:bg-white">
            <Settings className="h-5 w-5 text-coffee-800" />
          </button>
        </div>
      </div>

      <div className="relative -mt-6 px-6">
        <div className="relative z-20 flex items-center justify-around rounded-2xl bg-white p-4 shadow-float">
          <Stat label="publicId" value={publicId ?? '--'} accent="text-accent-pink" />
          <Divider />
          <Stat label="当前状态" value={currentEvent ? currentStatusLabel : '暂无'} accent="text-milk-500" />
          <Divider />
          <Stat label="当前事件" value={currentEvent?.eventId ?? '--'} accent="text-accent-blue" />
        </div>
      </div>

      <div className="space-y-6 px-6 pt-8">
        <Card className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Session</p>
          <div className="space-y-2 text-sm leading-7 text-coffee-800/70">
            <p>用户名草稿：{usernameDraft || '未填写'}</p>
            <p>publicId：{publicId || '未登录'}</p>
            <p>relationshipId：{relationshipLabel}</p>
          </div>
        </Card>

        <Card className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Current Flow</p>
          {currentEvent ? (
            <div className="space-y-2 text-sm leading-7 text-coffee-800/70">
              <p>标题：{currentEvent.title}</p>
              <p>事件 ID：{currentEvent.eventId}</p>
              <p>状态：{currentStatusLabel}</p>
            </div>
          ) : (
            <p className="text-sm leading-7 text-coffee-800/60">还没有进行中的事件，去调解室创建一个新的吧。</p>
          )}
        </Card>

        <Button
          fullWidth
          variant="danger"
          disabled={isLoggingOut}
          onClick={async () => {
            await logout();
            navigate('/login', { replace: true });
          }}
        >
          <LogOut className="mr-2 h-4 w-4" />
          退出登录
        </Button>
      </div>
    </div>
  );
}

function Divider() {
  return <div className="h-8 w-px bg-gray-100" />;
}

function Stat({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="text-center flex flex-col items-center justify-center">
      <span className={`block text-lg font-extrabold ${accent} mb-1`}>{value}</span>
      <span className="text-[10px] font-bold text-gray-400">{label}</span>
    </div>
  );
}
