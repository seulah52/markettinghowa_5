'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import type { AnalysisReport } from '@/lib/types';

interface Props { jobId: string; }

export default function MarketAnalysisReport({ jobId }: Props) {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [status, setStatus] = useState<'polling' | 'done' | 'error'>('polling');

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await apiClient.analysis.getReport(jobId);
      if (res.status === 'done') {
        setReport(res.data);
        setStatus('done');
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  if (status === 'polling') return <p className="text-center animate-pulse">분석 중...</p>;
  if (!report) return null;

  return (
    <section className="reveal space-y-8">
      <h2 className="text-2xl font-bold">{report.title}</h2>
      <p>{report.summary}</p>
    </section>
  );
}
