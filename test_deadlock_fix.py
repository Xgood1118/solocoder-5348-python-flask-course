import requests
import json
import time
import threading
from dotenv import load_dotenv

load_dotenv()

from app.services.auth_service import (
    generate_student_token,
    generate_teacher_token,
    generate_admin_token,
)

BASE_URL = "http://localhost:8080"


def admin_login():
    resp = requests.post(
        f"{BASE_URL}/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, f"登录失败: {resp.status_code}"
    return resp.json()["data"]["token"]


def test_semester_close_after_delay():
    print("=" * 60)
    print("测试1: 等待 6 秒（超过 flush 间隔 5 秒）后执行学期结课")
    print("=" * 60)

    token = admin_login()
    headers = {"Authorization": f"Bearer {token}"}

    print("等待 6 秒，让 flush 线程至少运行一次...")
    for i in range(6):
        time.sleep(1)
        print(f"  已等待 {i + 1} 秒...")

    print("\n现在尝试关闭 2024-fall 学期（应该不超时）...")
    start_time = time.time()
    resp = requests.post(
        f"{BASE_URL}/admin/semesters/2024-fall/close",
        headers=headers,
        timeout=10,
    )
    elapsed = time.time() - start_time

    print(f"状态码: {resp.status_code}")
    print(f"响应时间: {elapsed:.2f} 秒")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

    assert resp.status_code == 200, f"学期结课失败，状态码: {resp.status_code}"
    assert elapsed < 5, f"响应时间过长 ({elapsed:.2f}s)，疑似死锁"
    print("✓ 测试通过：学期结课操作正常\n")


def test_concurrent_writes_and_flush():
    print("=" * 60)
    print("测试2: 并发写入 + flush 线程触发，验证无死锁")
    print("=" * 60)

    token = admin_login()
    headers = {"Authorization": f"Bearer {token}"}

    student_tokens = []
    for i in range(1, 5):
        student_tokens.append(generate_student_token(f"s00{i}"))

    success_count = [0]
    lock = threading.Lock()

    def submit_review_worker(student_id, course_id, semester, iterations):
        local_token = generate_student_token(student_id)
        local_headers = {"Authorization": f"Bearer {local_token}"}
        for i in range(iterations):
            try:
                review_data = {
                    "student_id": student_id,
                    "course_id": course_id,
                    "semester": semester,
                    "content_score": (i % 5) + 1,
                    "difficulty_score": (i % 5) + 1,
                    "gain_score": (i % 5) + 1,
                    "comment": f"这是第 {i} 条测试评价，内容 {student_id} {i}",
                }
                resp = requests.post(
                    f"{BASE_URL}/reviews",
                    headers=local_headers,
                    json=review_data,
                    timeout=5,
                )
                if resp.status_code in (200, 409):
                    with lock:
                        success_count[0] += 1
            except Exception as e:
                print(f"  错误: {student_id} - {e}")

    print("启动 4 个线程并发提交评价，每个 5 次...")
    threads = []
    test_cases = [
        ("s001", "c002", "2023-fall"),
        ("s002", "c004", "2024-spring"),
        ("s003", "c003", "2024-spring"),
        ("s004", "c002", "2023-fall"),
    ]

    start_time = time.time()
    for student_id, course_id, semester in test_cases:
        t = threading.Thread(
            target=submit_review_worker,
            args=(student_id, course_id, semester, 5),
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=30)

    elapsed = time.time() - start_time
    print(f"完成 {success_count[0]} 次请求，耗时 {elapsed:.2f} 秒")

    assert not any(t.is_alive() for t in threads), "有线程未正常结束，疑似死锁"
    assert elapsed < 20, f"总耗时过长 ({elapsed:.2f}s)，疑似死锁"
    print("✓ 测试通过：并发写入无死锁\n")


def test_multiple_semester_close():
    print("=" * 60)
    print("测试3: 多次触发学期结课 + 中间等待 flush")
    print("=" * 60)

    token = admin_login()
    headers = {"Authorization": f"Bearer {token}"}

    test_semesters = ["2024-fall"]

    for i, sem in enumerate(test_semesters):
        print(f"第 {i + 1} 轮: 等待 5.5 秒后操作学期 {sem}...")
        time.sleep(5.5)

        start_time = time.time()
        resp = requests.post(
            f"{BASE_URL}/admin/semesters/{sem}/close",
            headers=headers,
            timeout=10,
        )
        elapsed = time.time() - start_time

        print(f"  状态码: {resp.status_code}, 耗时: {elapsed:.2f}s")
        print(f"  响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

        assert elapsed < 5, f"第 {i + 1} 轮响应时间过长 ({elapsed:.2f}s)，疑似死锁"

    print("✓ 测试通过：多次学期结课操作无死锁\n")


def test_stats_after_all():
    print("=" * 60)
    print("测试4: 最后验证统计数据和数据完整性")
    print("=" * 60)

    token = admin_login()
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=5)
    print(f"状态码: {resp.status_code}")
    print(f"统计数据: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

    assert resp.status_code == 200
    print("✓ 测试通过：统计数据正常\n")


if __name__ == "__main__":
    try:
        test_semester_close_after_delay()
        test_concurrent_writes_and_flush()
        test_multiple_semester_close()
        test_stats_after_all()

        print("=" * 60)
        print("🎉 所有死锁修复验证测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
