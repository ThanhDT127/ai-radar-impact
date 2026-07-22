"""Khoá cấu hình cron của job bản tin.

`CLAUDE.md` ghi hai cách cấu hình SAI mà người sau dễ rơi vào, nhưng gotcha là văn bản —
không chặn được ai đổi code. Test này mới là hàng rào:

1. `IntervalTrigger(days=3)` — APScheduler dùng jobstore trong bộ nhớ nên mỗi lần restart
   mốc kế tiếp tính lại từ lúc start ⇒ nhịp trôi dạt.
2. cron `day='*/3'` — là ngày-TRONG-THÁNG: 1,4,…,31 rồi nhảy mùng 1 (cách nhau 1 ngày).

Và timezone phải truyền thẳng vào trigger: `CronTrigger` dựng sẵn KHÔNG kế thừa timezone
của scheduler, thiếu nó là job rơi về UTC (lệch 7 tiếng so với giờ VN).
"""

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler import create_scheduler


def _delivery_jobs(scheduler):
    return [j for j in scheduler.get_jobs() if j.id == "delivery_brief"]


def test_delivery_job_registered_only_when_enabled():
    assert _delivery_jobs(create_scheduler(include_pipeline=False, include_delivery=False)) == []
    assert len(_delivery_jobs(create_scheduler(include_pipeline=False, include_delivery=True))) == 1


def test_delivery_job_uses_cron_not_interval():
    """IntervalTrigger(days=3) trôi mốc sau mỗi restart — không được dùng."""
    job = _delivery_jobs(create_scheduler(include_pipeline=False, include_delivery=True))[0]
    assert isinstance(job.trigger, CronTrigger)
    assert not isinstance(job.trigger, IntervalTrigger)


def test_delivery_job_runs_on_weekdays_not_day_of_month():
    """Nhịp theo NGÀY TRONG TUẦN; `day='*/3'` là ngày-trong-tháng nên sai ở ranh giới tháng."""
    job = _delivery_jobs(create_scheduler(include_pipeline=False, include_delivery=True))[0]
    fields = {f.name: str(f) for f in job.trigger.fields}

    assert fields["day_of_week"] == settings.delivery_digest_days
    assert fields["hour"] == str(settings.delivery_digest_hour)
    # `day` phải để mặc định "*" — nếu có bước nhảy ở đây là đã rơi vào bẫy day-of-month
    assert fields["day"] == "*"


def test_delivery_job_timezone_is_vietnam():
    """CronTrigger dựng sẵn không kế thừa timezone của scheduler — phải truyền thẳng."""
    job = _delivery_jobs(create_scheduler(include_pipeline=False, include_delivery=True))[0]
    assert "Ho_Chi_Minh" in str(job.trigger.timezone)


def test_no_alert_job_remains():
    """Alert tức thời đã bỏ hẳn — không job nào chạy theo phút nữa."""
    scheduler = create_scheduler(include_pipeline=False, include_delivery=True)
    assert [j.id for j in scheduler.get_jobs()] == ["delivery_brief"]
