import { useState } from 'react'
import { Bar as RBar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CheckCircle2 } from 'lucide-react'
import { api } from '../api/client.js'
import { useApp } from '../lib/appContext.js'
import { COLOR, SENT, nf, pct } from '../lib/format.js'
import useApi from '../lib/useApi.js'
import { Card, ChartTip, ErrorBox, Loading, Pager, Segmented, SentBadge, Stars, axisProps } from '../components/ui.jsx'

const NAME = { LR: 'Logistic Regression', NB: 'Multinomial Naive Bayes', SVM: 'Linear SVM (hiệu chỉnh xác suất)', B0: 'Đường cơ sở: luôn 5 sao' }

export default function ModelTab() {
  const m = useApi(() => api.modelMetrics(), [])
  const kw = useApi(() => api.modelKeywords(20), [])
  const [cm, setCm] = useState(3)
  if (m.loading) return <Loading h="h-80" />
  if (m.error) return <ErrorBox error={m.error} onRetry={m.reload} />
  const d = m.data
  const sel = d.models.find((x) => x.selected)
  const sp = d.split
  return (
    <div className="space-y-5">
      <div className="grid lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1.4fr)] gap-5">
        <Card title="Mô hình đang dùng để dự đoán">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-primarySoft text-primary flex items-center justify-center"><CheckCircle2 size={24} /></div>
            <div className="flex-1">
              <div className="text-[18px] font-semibold text-ink">{NAME[sel.model]}</div>
              <div className="text-[13px] text-muted">{sel.params} · huấn luyện lúc {d.trained_at?.replace('T', ' ')}</div>
              <div className="flex gap-6 mt-3">
                <Big v={nf(sel.f1_macro3, 3)} l="F1-macro 3 lớp" />
                <Big v={nf(sel.f1_neg, 3)} l="F1 lớp tiêu cực" />
                <Big v={pct(sel.acc5)} l="Đúng chính xác số sao" />
              </div>
            </div>
          </div>
          <div className="mt-4 rounded-lg bg-slate-50 p-3 text-[13px] leading-relaxed text-text">
            Học từ <b className="text-ink">{nf(sp.train)}</b> đánh giá đã làm sạch, kiểm tra trên <b className="text-ink">{nf(sp.test)}</b> đánh giá chưa từng thấy
            (chia 80/20 phân tầng theo số sao, random_state = {sp.random_state}){sp.sampled ? `; lấy mẫu phân tầng ${nf(sp.n_used)} trong ${nf(sp.n_dataset)} đánh giá để huấn luyện nhanh` : ''}.
            Văn bản = tiêu đề + nội dung, chuyển chữ thường, tách “n't” → “not”, vector TF-IDF 1–2-gram ({nf(d.vectorizer?.n_features)} đặc trưng).
            Logistic Regression là cấu hình đã chọn trên tập validation ở thực nghiệm (F1-macro 3 lớp cao nhất – thước đo chính vì dữ liệu lệch mạnh về 5 sao)
            và có hệ số để giải thích từ khóa; tập kiểm tra ở đây chỉ dùng để báo cáo, không dùng để chọn lại mô hình.
          </div>
        </Card>
        <Card title="So sánh các mô hình trên tập kiểm tra" subtitle="F1-macro 3 lớp (tiêu cực / trung tính / tích cực) – thước đo chính, đo trên tập kiểm tra">
          <div className="h-48">
            <ResponsiveContainer>
              <BarChart data={d.models} layout="vertical" margin={{ top: 0, right: 48, bottom: 0, left: 0 }}>
                <XAxis type="number" domain={[0, 1]} hide />
                <YAxis type="category" dataKey="model" {...axisProps} width={44} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} content={<ChartTip labelFormat={(k) => NAME[k]} rows={(x) => [['F1-macro', nf(x.f1_macro3, 3), x.selected ? COLOR.primary : COLOR.axis], ['Accuracy 5 sao', pct(x.acc5)], ['Thời gian học', `${nf(x.fit_seconds, 1)} s`]]} />} />
                <RBar dataKey="f1_macro3" barSize={20} radius={[0, 4, 4, 0]} isAnimationActive={false}>
                  {d.models.map((x) => <Cell key={x.model} fill={x.selected ? COLOR.primary : x.model === 'B0' ? '#dfe4ea' : '#b8c2cd'} />)}
                  <LabelList dataKey="f1_macro3" position="right" formatter={(v) => nf(v, 3)} style={{ fontSize: 12, fill: COLOR.text }} />
                </RBar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="Bảng chỉ số chi tiết" pad={false}>
        <div className="overflow-x-auto">
          <table className="tbl">
            <thead>
              <tr>
                <th>Mô hình</th>
                <th>Tham số</th>
                <th className="text-right">F1-macro</th>
                <th className="text-right">Precision / Recall (macro)</th>
                <th className="text-right">F1 tiêu cực / trung tính / tích cực</th>
                <th className="text-right">Precision / Recall tiêu cực</th>
                <th className="text-right">Accuracy 3 lớp / 5 sao</th>
                <th className="text-right">MAE (sao)</th>
                <th className="text-right">Thời gian học</th>
              </tr>
            </thead>
            <tbody>
              {d.models.map((x) => (
                <tr key={x.model} className={x.selected ? 'bg-primarySoft/50' : ''}>
                  <td className="text-ink font-medium whitespace-nowrap">
                    {x.selected && <CheckCircle2 size={13} className="inline text-primary mr-1 -mt-0.5" />}
                    {NAME[x.model]}
                  </td>
                  <td className="text-muted whitespace-nowrap">{x.params}</td>
                  <td className="text-right font-semibold text-ink">{nf(x.f1_macro3, 3)}</td>
                  <td className="text-right whitespace-nowrap">{nf(x.prec_macro3, 3)} / {nf(x.rec_macro3, 3)}</td>
                  <td className="text-right whitespace-nowrap">{nf(x.f1_neg, 3)} / {nf(x.f1_neu, 3)} / {nf(x.f1_pos, 3)}</td>
                  <td className="text-right whitespace-nowrap">{nf(x.prec_neg, 3)} / {nf(x.rec_neg, 3)}</td>
                  <td className="text-right whitespace-nowrap">{pct(x.acc3)} / {pct(x.acc5)}</td>
                  <td className="text-right">{nf(x.mae, 3)}</td>
                  <td className="text-right whitespace-nowrap">{nf(x.fit_seconds, 1)} s</td>
                </tr>
              ))}
            </tbody>
          </table>
