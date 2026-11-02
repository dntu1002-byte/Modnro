# CI build Windows (cần bạn bật thủ công)
Token của mình không có quyền `workflow` nên không đẩy được vào `.github/workflows/`.
Để có build + test THẬT trên Windows (csc.exe, không cần máy Windows của bạn): chép `autocaptcha-windows.yml` vào `.github/workflows/` (trên web GitHub: Add file → Create new file), commit, rồi vào tab Actions để xem kết quả và tải artifact `AutoCaptcha-exe-windows`.
Workflow chưa từng chạy, nên chưa biết có lỗi cú pháp/đường dẫn hay không.
