"""Router predict – UC-04: tự nhập đánh giá để dự đoán (FR-14 – FR-16).

Sprint XD2 (PB-06, tích hợp): mã sản phẩm nhập kèm được chuẩn hóa giống API #13, #15, #16 và tra trong bảng sản phẩm.
Có mã → trả bối cảnh sản phẩm (số đánh giá, điểm TB, chỉ số hài lòng, mức rủi ro) để so với kết quả dự đoán;
không có mã trong dữ liệu → vẫn dự đoán theo nội dung nhưng product = null kèm ghi chú, giao diện không mở chi tiết
sản phẩm (trước đây nút “Xem sản phẩm” mở ngăn chi tiết toàn lỗi 404).
"""
import time

from fastapi import APIRouter

from backend.core import config as C
from backend.core.deps import require_model
from backend.core.state import STATE
from backend.core.errors import ApiError
from backend.schemas.api import ErrorResponse, PredictRequest, PredictResponse
from backend.services import ai_service as AI

router = APIRouter(tags=["Dự đoán"])


@router.post("/predict", response_model=PredictResponse, summary="Dự đoán số sao, cảm xúc, chỉ số hài lòng của một đánh giá",
             description="Dùng mô hình đã huấn luyện trên dữ liệu đã làm sạch, chuẩn hóa của phiên hiện tại; văn bản nhập vào "
                         "được chuẩn hóa giống dữ liệu huấn luyện (chữ thường, n't → not, TF-IDF 1–2-gram).",
             responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
def predict(req: PredictRequest):
    require_model()
    if len(req.text.split()) < C.MIN_WORDS_PREDICT:
        raise ApiError(422, "TEXT_TOO_SHORT", f"Nội dung cần tối thiểu {C.MIN_WORDS_PREDICT} từ")
    t0 = time.perf_counter()
    out = AI.predict_full(req.text, req.summary)
    pid = (req.product_id or "").strip().upper() or None
    out["product_id"], out["product"] = pid, None
    if pid:
        out["product"] = _product_context(pid)
        if out["product"] is None:
            msg = f"Mã sản phẩm {pid} không có trong dữ liệu hiện tại – kết quả chỉ dựa trên nội dung đánh giá."
            out["note"] = f"{out['note']} {msg}" if out.get("note") else msg
    out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return out


def _product_context(pid: str) -> dict | None:
    """Một dòng của bảng sản phẩm (cùng nguồn với API #10 – tab Sản phẩm & cảnh báo) để số liệu khớp giữa các màn hình."""
    p = STATE.products
    if p is None:
        return None
    row = p[p.product_id == pid]
    if row.empty:
        return None
    r = row.iloc[0]
    return {"product_id": pid, "n_reviews": int(r.n_reviews), "avg_score": round(float(r.avg_score), 4),
            "satisfaction_index": round(float(C.satisfaction_index(r.avg_score)), 2), "neg_rate": round(float(r.neg_rate), 4),
            "risk_level": r.risk_level, "first_month": r.get("first_month"), "last_month": r.get("last_month")}
