import { zodResolver } from '@hookform/resolvers/zod';
import { UserPlus } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { DeviceFrame } from '@/components/layout/DeviceFrame';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/hooks';

const schema = z
  .object({
    username: z.string().min(3, '用户名至少 3 位'),
    password: z.string().min(8, '密码至少 8 位'),
    confirmPassword: z.string().min(8, '确认密码至少 8 位'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  });

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { register: registerUser, isRegistering, registerError, setUsernameDraft } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const locationState = location.state as { from?: string } | null;

  return (
    <DeviceFrame className="items-stretch">
      <div className="flex h-full w-full flex-col bg-milk-50">
        <div className="bg-milk-200 px-6 pb-12 pt-16">
          <div className="flex items-center gap-3">
            <div className="rounded-3xl bg-white/70 p-3 text-coffee-900">
              <UserPlus className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Create Account</p>
              <h1 className="text-3xl font-extrabold text-coffee-900">加入 LoveMediator</h1>
            </div>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-7 text-coffee-800/70">
            先创建账号，后面就可以通过邀请页加入事件处理流程。
          </p>
        </div>

        <div className="-mt-8 flex-1 px-6 pb-8">
          <Card className="space-y-4">
            <form
              className="space-y-4"
              onSubmit={handleSubmit(async (values) => {
                await registerUser({ username: values.username, password: values.password });
                setUsernameDraft(values.username);
                navigate('/login', {
                  replace: true,
                  state: {
                    registered: true,
                    from: locationState?.from,
                  },
                });
              })}
            >
              <Input label="用户名" placeholder="alice" error={errors.username?.message} {...register('username')} />
              <Input
                label="密码"
                type="password"
                placeholder="至少 8 位"
                error={errors.password?.message}
                {...register('password')}
              />
              <Input
                label="确认密码"
                type="password"
                placeholder="再输入一次密码"
                error={errors.confirmPassword?.message}
                {...register('confirmPassword')}
              />
              {registerError ? <p className="text-sm font-semibold text-red-400">{registerError}</p> : null}
              <Button fullWidth type="submit" disabled={isRegistering}>
                {isRegistering ? <LoadingSpinner /> : '注册'}
              </Button>
            </form>

            <p className="text-center text-sm text-coffee-800/60">
              已经有账号？
              <Link className="ml-1 font-bold text-coffee-900" to="/login" state={{ from: locationState?.from }}>
                返回登录
              </Link>
            </p>
          </Card>
        </div>
      </div>
    </DeviceFrame>
  );
}
