"""Cấu hình chung cho test — giữ cho bộ test HERMETIC.

VÌ SAO FILE NÀY TỒN TẠI (03/08/2026): `settings` đọc từ `.env` của máy đang chạy, nên bộ test
vốn thừa hưởng cấu hình cá nhân của người chạy. Bật `CHAT_WEB_FALLBACK_ENABLED=true` trong
`.env` để dùng thật ⇒ **51 test đỏ ngay lập tức**, không phải vì code sai mà vì đường tra cứu
thêm một truy vấn quota mà các fake session không lường (`IndexError: pop from empty list`).

Đó là một chế độ hỏng tệ theo cả hai chiều:
- Đỏ giả: sửa `.env` cho môi trường thật làm vỡ CI, không liên quan gì tới thay đổi code.
- **Xanh giả, nguy hiểm hơn**: một người có `.env` bật cờ sẽ chạy một bộ test khác hẳn người
  không bật, và cả hai đều tưởng mình đang gác cùng một thứ.

Nên: mọi cờ TÍNH NĂNG được ghim về **mặc định shipped** cho toàn bộ test. Test nào cần đường
kia thì tự bật bằng `monkeypatch` — tường minh tại chỗ, không phụ thuộc môi trường.
"""

import pytest

from app.config import settings

# Cờ tính năng + giá trị mặc định trong `config.py`. Ghim, KHÔNG đọc từ `.env`.
_SHIPPED_DEFAULTS = {
    "chat_web_fallback_enabled": False,
}


@pytest.fixture(autouse=True)
def _pin_feature_flags(monkeypatch):
    """Ghim cờ tính năng về mặc định shipped cho MỌI test.

    `autouse` có chủ đích: một test quên ghim sẽ không đỏ ngay mà chỉ đo sai trong im lặng,
    nên đây phải là hành vi mặc định chứ không phải thứ người viết test phải nhớ.
    """
    for name, value in _SHIPPED_DEFAULTS.items():
        monkeypatch.setattr(settings, name, value)
