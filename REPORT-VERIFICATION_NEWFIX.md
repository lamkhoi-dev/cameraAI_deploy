# Báo cáo kiểm tra — Các chi tiết đã xác minh

Ngày: 2026-05-22
Người tạo: Tự động (assistant)

## Tóm tắt
File này tổng hợp các mục tôi đã kiểm tra trong repository, nêu rõ những chức năng đã được triển khai, vị trí file liên quan và hướng dẫn kiểm thử ngắn. Đây là báo cáo kiểm tra/đánh giá (không bao gồm sửa mã tự động).

---

## 1. Cấu hình "Thời gian hiển thị" (Display interval)
- Trạng thái: Đã triển khai.
- File liên quan: `backend/models/camera.py` (trường `display_interval_seconds`).
- Logic: `GET /api/cameras/{camera_id}/display_image` trong `backend/routers/cameras.py` lấy `display_interval` (query hoặc giá trị camera), truy vấn `persons`/`vehicles` trong khoảng thời gian đó, chọn kết quả có `confidence` cao nhất rồi trả ảnh (hoặc trả fallback/base64 nếu không có kết quả AI).
- Kiểm thử đề xuất: Gọi API `GET /api/cameras/<CAM>/display_image?display_interval=5&fallback_seconds=5` và kiểm tra `type` (`ai` / `fallback`) cùng trường `confidence`.

## 2. Cơ chế chụp ảnh fallback (Snapshot)
- Trạng thái: Đã triển khai.
- File liên quan: `backend/services/snapshot_service.py` (background snapshot cache), `backend/routers/cameras.py` (sử dụng cache hoặc on-demand capture qua `camera_service.test_camera_connection`).
- Ghi chú: SnapshotService chạy vòng lặp poll và lưu base64 thumbnail, TTL dựa trên `fallback_seconds` per-camera.
- Kiểm thử đề xuất: Gọi `GET /api/cameras/<CAM>/display_image` khi không có record AI -> nhận `type: "fallback"`.

## 3. FPS xử lý / Drop frames (AI Real-time)
- Trạng thái: Đã triển khai.
- File liên quan: `ai_engine/utils/frame_grabber.py` (thuật toán grab/grab+retrieve và `processing_fps`/`frame_interval`), `ai_engine/engine.py` (sử dụng skip frames / adaptive skipping), `run_engine.py` (phiên bản standalone engine có logic skip frames khi dùng `process_camera`).
- Logic: `FrameGrabber` tính `frame_interval` từ `processing_fps`; khi chạy, nếu thời điểm chưa tới `next_process_time` thì chỉ `cap.grab()` để bỏ frame (drop) và không gọi inference. `AIEngine`/`run_engine.py` còn sử dụng skip-frames/adaptive skipping để giảm tải.
- Kiểm thử đề xuất: Khởi engine, quan sát logs fps và `FrameGrabber.fps`; so sánh `processing_fps` cấu hình với số frames thực tế processed.

## 4. Lưu và sử dụng ROI (Vùng AI xử lý & Vùng tuần tra)
- Trạng thái: Đã triển khai.
- File liên quan:
  - Frontend: `frontend/src/components/RegionEditor.tsx` (vẽ, trả normalized coords)
  - Backend lưu: `backend/services/camera_service.py` (`ai_region_json` / `patrol_region_json`), DB schema `cameras` đã có các cột này (migrations có `ai_region_json`, `patrol_region_json`).
  - AI side: `ai_engine/utils/roi_utils.py` (`apply_roi_mask`), `run_engine.py` và `ai_engine/processors/*` áp mask/kiểm tra điểm trong đa giác (`_point_in_polygon`).
- Logic: Khi chạy detection/patrol, hệ thống convert normalized ROI → pixel, áp mask hoặc kiểm tra center-of-bbox trong polygon để chỉ báo sự kiện nếu đối tượng nằm trong ROI.
- Kiểm thử đề xuất: Vẽ ROI trong UI, chụp định kỳ (patrol) hoặc tạo event real-time; kiểm tra rằng chỉ các đối tượng trong ROI sinh alert (kiểm tra `/api/alerts` và `alerts` DB table).

## 5. Giám sát định kỳ (Patrol / monitoring_interval_minutes)
- Trạng thái: Đã triển khai.
- File liên quan: `run_engine.py` — hàm `patrol_camera` thực hiện vòng lặp, chụp frame định kỳ theo `monitoring_interval_minutes` (lấy từ camera config), gọi `_detect_patrol_violations` và `push_alert` nếu có vi phạm.
- Cơ chế: Worker (loop + wait), không dùng cron. Nếu capture thất bại (camera unreachable) sẽ ghi log `Patrol capture failed` và bỏ qua lần này.
- Kiểm thử đề xuất: Set `monitoring_interval_minutes` nhỏ (1), chạy `run_engine.py`, quan sát logs và kiểm tra `GET /api/alerts` cho alert mới; mô phỏng mất kết nối để kiểm tra xử lý lỗi.

## 6. Lưu lịch sử và hiển thị
- Trạng thái: Đã triển khai.
- File liên quan: `backend/routers/ai_ingest.py` (nhận `POST /api/ai/alerts`), model `backend/models/alert.py` (lưu `camera_id`, `alert_type`, `confidence`, `snapshot_base64`, `timestamp`), API lịch sử: `GET /api/alerts` trong `backend/routers/history.py`.
- Kiểm thử đề xuất: Kiểm tra endpoint `GET /api/alerts` hoặc truy vấn SQL trực tiếp trên bảng `alerts`.

---

## Ghi chú và bước tiếp theo
- Tôi chỉ thực hiện đọc và xác minh logic trong mã nguồn — chưa chạy các service trên môi trường của bạn. Để nghiệm thu đầy đủ, tôi có thể:
  - (A) Chạy một kịch bản test tự động (script) để mô phỏng captures và kiểm tra `/api/alerts` (offline), hoặc
  - (B) Giúp bạn chạy `run_engine.py` và thực hiện các `curl` kiểm tra trực tiếp trên môi trường của bạn.

Muốn tôi tạo script test tự động (A) hay hướng dẫn chi tiết để bạn chạy (B)?
