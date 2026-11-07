import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, Lightbulb, Sparkles, Target } from 'lucide-react'
import { Note, ReviewQuote } from './ui.jsx'

const SEV = { cao: ['#d03b3b', '#fdecec'], 'trung bình': ['#b57300', '#fff4dc'], thấp: ['#55606b', '#f1f3f5'] }

export function SevBadge({ level }) {
  const [c, bg] = SEV[level] || SEV.thấp
  return <span className="rounded-full px-2 py-0.5 text-[11.5px] font-medium whitespace-nowrap" style={{ color: c, background: bg }}>Mức {level}</span>
}

// Kết quả phân tích nguyên nhân – giải pháp (FR-26, FR-27): mỗi nguyên nhân kèm đánh giá bằng chứng có thật
export default function InsightView({ data }) {
  if (!data) return null
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-[12px] text-muted">
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${data.source === 'gemini' ? 'bg-aiSoft text-ai' : 'bg-slate-100 text-slate-600'}`}>
          <Sparkles size={12} />{data.source === 'gemini' ? `Gemini · ${data.model}` : 'Phân tích theo quy tắc'}
        </span>
        {data.cached && <span className="rounded-full bg-slate-100 px-2 py-0.5">Kết quả đã lưu</span>}
        <span>{data.created_at}</span>
        {data.n_reviews_sent != null && <span>· {data.n_reviews_sent} đánh giá được phân tích</span>}
        {data.dropped_causes > 0 && <span>· loại {data.dropped_causes} nguyên nhân không có bằng chứng hợp lệ</span>}
        {data.n_calls > 1 && <span>· gọi Gemini {data.n_calls} lần (đã yêu cầu viết lại phần thiếu)</span>}
      </div>
      {data.note && <Note tone={data.source === 'gemini' ? 'info' : 'warn'}>{data.note}</Note>}
      {data.causes.length === 0 && <div className="text-[13px] text-muted">Không xác định được nguyên nhân có bằng chứng từ các đánh giá hiện có.</div>}
      {data.causes.map((c, i) => <Cause key={i} c={c} i={i} sol={data.solutions.filter((s) => s.cause_index === i)} />)}
    </div>
  )
}

function Cause({ c, i, sol }) {
  const [open, setOpen] = useState(i === 0)
  return (
    <div className="rounded-xl border border-line bg-white">
      <div className="px-4 py-3">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 w-5 h-5 rounded-full bg-ink text-white text-[11px] flex items-center justify-center shrink-0">{i + 1}</span>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2"><span className="font-semibold text-ink text-[14px]">{c.title}</span><SevBadge level={c.severity} /></div>
            <p className="text-[13px] text-text mt-1 leading-relaxed">{c.description}</p>
          </div>
        </div>
        {sol.map((s, k) => (
          // giải pháp thiếu ý (hành động bị cắt, quá ngắn) hiện viền vàng và lý do, để người bán không áp dụng nhầm
          <div key={k} className={`mt-3 ml-7 rounded-lg border px-3 py-2 text-[13px] ${s.complete === false ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50/70 border-emerald-100'}`}>
            <div className="flex items-start gap-2"><Lightbulb size={15} className={`${s.complete === false ? 'text-amber-600' : 'text-emerald-700'} mt-0.5 shrink-0`} /><div className="flex-1"><span className="text-ink">{s.action}</span> <SevBadge level={s.priority} /></div></div>
            <div className="flex items-start gap-2 mt-1 text-[12.5px] text-muted"><Target size={14} className="mt-0.5 shrink-0" />Theo dõi: {s.kpi}</div>
            {s.complete === false && <div className="flex items-start gap-2 mt-1 text-[12px] text-amber-700"><AlertTriangle size={13} className="mt-0.5 shrink-0" />Giải pháp chưa đủ ý: {s.problem}. Bấm “Gọi lại” để Gemini viết lại.</div>}
          </div>
        ))}
        <button className="ml-7 mt-2 inline-flex items-center gap-1 text-[12.5px] text-primary" onClick={() => setOpen(!open)}>
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}{c.evidence.length} đánh giá bằng chứng (#{c.evidence_ids.join(', #')})
        </button>
      </div>
      {open && <div className="px-4 pb-4 ml-7 space-y-2">{c.evidence.map((e) => <ReviewQuote key={e.review_id} r={e} />)}</div>}
    </div>
  )
}
