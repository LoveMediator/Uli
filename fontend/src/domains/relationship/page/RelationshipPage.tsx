import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Input } from '@/shared/ui/Input';
import { Loader2 } from 'lucide-react';
import { useCreateRelationship } from '@/domains/relationship/hooks/useCreateRelationship';
import { useQueryClient } from '@tanstack/react-query';

const RelationshipPage = () => {
  const navigate = useNavigate();
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { createInvite, acceptInvite } = useCreateRelationship();
  const queryClient = useQueryClient();

  const handleCreateInvite = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await createInvite.mutateAsync();
      alert(`邀请码已生成：${result.invite_code}\n请将此邀请码分享给您的伴侣`);
    } catch (err) {
      setError('生成邀请码失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJoinRelationship = async () => {
    if (!inviteCode.trim()) {
      setError('请输入邀请码');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await acceptInvite.mutateAsync(inviteCode);
      await queryClient.invalidateQueries({ queryKey: ['relationships'] });
      alert('关系绑定成功！');
      navigate('/app/home');
    } catch (err) {
      setError('邀请码无效或已过期');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 min-h-screen bg-milk-50">
      <div className="w-full max-w-md">
        <Card className="p-8 shadow-soft">
          <h1 className="text-2xl font-bold text-center text-coffee-800 mb-6">关系绑定</h1>
          
          {error && (
            <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-md">
              <h3 className="font-medium mb-1">错误</h3>
              <p>{error}</p>
            </div>
          )}

          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4 text-coffee-700">创建邀请</h2>
              <p className="text-sm text-gray-600 mb-4">点击下方按钮生成邀请码，分享给您的伴侣</p>
              <Button 
                fullWidth
                onClick={handleCreateInvite}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  '生成邀请码'
                )}
              </Button>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h2 className="text-lg font-semibold mb-4 text-coffee-700">加入关系</h2>
              <p className="text-sm text-gray-600 mb-4">输入伴侣分享的邀请码</p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="inviteCode" className="block text-sm font-medium text-gray-700">邀请码</label>
                  <Input
                    id="inviteCode"
                    value={inviteCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInviteCode(e.target.value)}
                    placeholder="请输入邀请码"
                    disabled={isSubmitting}
                  />
                </div>
                <Button 
                  fullWidth
                  onClick={handleJoinRelationship}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      绑定中...
                    </>
                  ) : (
                    '绑定关系'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>已经有绑定关系了？</p>
          <Button 
                  variant="ghost" 
                  className="text-coffee-800 hover:text-coffee-900 p-0"
                  onClick={() => navigate('/app/home')}
                >
                  返回首页
                </Button>
        </div>
      </div>
    </div>
  );
};

export { RelationshipPage };