import { zodResolver } from '@hookform/resolvers/zod';
import { HeartHandshake } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { DeviceFrame } from '@/components/layout/DeviceFrame';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/hooks';

const schema = z.object({
  username: z.string().min(3, '用户名至少 3 位'),
  password: z.string().min(8, '密码至少 8 位'),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoggingIn, loginError, usernameDraft, setUsernameDraft } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: usernameDraft,
      password: '',
    },
  });

  const locationState = location.state as { from?: string; registered?: boolean } | null;
  const from = locationState?.from;

  return (
    <DeviceFrame className="items-stretch">
      <div className="flex h-full w-full flex-col bg-milk-50">
        <div className="bg-milk-200 px-6 pb-12 pt-16">
          <div className="flex items-center gap-3">
            <div className="rounded-3xl bg-white/70 p-3 text-coffee-900">
              <HeartHandshake className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">LoveMediator</p>
              <h1 className="text-3xl font-extrabold text-coffee-900">欢迎回来</h1>
            </div>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-7 text-coffee-800/70">
            登录后继续完成调解、查看裁判结果和吵架日历。
          </p>
        </div>

        <div className="-mt-8 flex-1 px-6 pb-8">
          <Card className="space-y-4">
            {locationState?.registered ? (
              <div className="rounded-2xl bg-accent-green/20 px-4 py-3 text-sm font-semibold text-coffee-900">
                注册成功，现在可以直接登录了。
              </div>
            ) : null}
            <form
              className="space-y-4"
              onSubmit={handleSubmit(async (values) => {
                setUsernameDraft(values.username);
                await login(values);
                navigate(from ?? '/app/home', { replace: true });
              })}
            >
              <Input
                label="用户名"
                placeholder="alice"
                error={errors.username?.message}
                {...register('username', {
                  onBlur: (event) => setUsernameDraft(event.target.value),
                })}
              />
              <Input
                label="密码"
                type="password"
                placeholder="Secret123!"
                error={errors.password?.message}
                {...register('password')}
              />
              {loginError ? <p className="text-sm font-semibold text-red-400">{loginError}</p> : null}
              <Button fullWidth type="submit" disabled={isLoggingIn}>
                {isLoggingIn ? <LoadingSpinner /> : '登录'}
              </Button>
            </form>

            <div className="rounded-3xl bg-milk-50 p-4 text-sm text-coffee-800/70">
              <p className="font-bold text-coffee-900">联调 seed 账号</p>
              <p className="mt-2">A：alice / Secret123!</p>
              <p>B：bob / Secret123!</p>
            </div>

            <p className="text-center text-sm text-coffee-800/60">
              还没有账号？
              <Link className="ml-1 font-bold text-coffee-900" to="/register" state={{ from }}>
                去注册
              </Link>
            </p>
          </Card>
        </div>
      </div>
    </DeviceFrame>
  );
}
