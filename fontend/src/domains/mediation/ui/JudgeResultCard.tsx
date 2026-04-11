import { Scale, Sparkles } from 'lucide-react';
import type { JudgeResultData } from '@/shared/api/types';
import { Card } from '@/shared/ui';

type JudgeResultCardProps = {
  result: JudgeResultData;
};

export function JudgeResultCard({ result }: JudgeResultCardProps) {
  return (
    <Card className="space-y-4 border-milk-100">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-milk-100 p-3 text-coffee-800">
          <Scale className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Judge Result</p>
          <h3 className="text-lg font-extrabold text-coffee-900">AI 裁决结果</h3>
        </div>
      </div>

      <div className="rounded-3xl bg-milk-50 p-4 text-sm leading-7 text-coffee-800">{result.objectiveSummary}</div>

      <div className="grid gap-3">
        <InsightBlock title="触发点" items={result.analysis.triggers} />
        <InsightBlock title="误解来源" items={result.analysis.misunderstandings} />
        <InsightBlock title="给 A 的建议" items={result.analysis.adviceForA} />
        <InsightBlock title="给 B 的建议" items={result.analysis.adviceForB} />
      </div>
    </Card>
  );
}

function InsightBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-3xl border border-milk-100 bg-white px-4 py-3">
      <div className="mb-2 flex items-center gap-2 text-coffee-900">
        <Sparkles className="h-4 w-4 text-accent-pink" />
        <span className="text-sm font-bold">{title}</span>
      </div>
      <ul className="space-y-2 text-sm text-coffee-800/80">
        {items.length > 0 ? items.map((item) => <li key={item}>· {item}</li>) : <li>暂无内容</li>}
      </ul>
    </div>
  );
}
