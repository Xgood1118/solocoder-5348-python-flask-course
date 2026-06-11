import requests
import json
import sys
from dotenv import load_dotenv

load_dotenv()

base_url = "http://localhost:8080"

def test_healthz():
    print("=== 1. 健康检查 ===")
    resp = requests.get(f"{base_url}/healthz")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    assert resp.status_code == 200
    print("✓ 通过\n")

def test_admin_login():
    print("=== 2. 管理员登录 ===")
    resp = requests.post(
        f"{base_url}/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    assert result["code"] == 0
    token = result["data"]["token"]
    print("✓ 通过\n")
    return token

def test_courses(token):
    print("=== 3. 获取课程列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{base_url}/courses", headers=headers)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"课程数量: {len(result['data']['courses'])}")
    print(f"第一门课: {json.dumps(result['data']['courses'][0], ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    assert len(result["data"]["courses"]) > 0
    print("✓ 通过\n")

def test_students(token):
    print("=== 4. 获取学生列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{base_url}/students", headers=headers)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"学生数量: {len(result['data']['students'])}")
    assert resp.status_code == 200
    assert len(result["data"]["students"]) > 0
    print("✓ 通过\n")

def test_teachers(token):
    print("=== 5. 获取教师列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{base_url}/teachers", headers=headers)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"教师数量: {len(result['data']['teachers'])}")
    assert resp.status_code == 200
    assert len(result["data"]["teachers"]) > 0
    print("✓ 通过\n")

def test_admin_stats(token):
    print("=== 6. 管理员统计 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{base_url}/admin/stats", headers=headers)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    print("✓ 通过\n")

def test_student_available_courses():
    print("=== 7. 学生可评课程 ===")
    from app.services.auth_service import generate_student_token
    student_token = generate_student_token("s001")
    headers = {"Authorization": f"Bearer {student_token}"}
    resp = requests.get(f"{base_url}/students/s001/available-courses", headers=headers)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"可评课程数量: {len(result['data']['courses'])}")
    print(f"可评课程: {json.dumps(result['data']['courses'], ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    print("✓ 通过\n")
    return student_token

def test_submit_review(student_token):
    print("=== 8. 提交评价 ===")
    headers = {"Authorization": f"Bearer {student_token}"}
    review_data = {
        "student_id": "s001",
        "course_id": "c001",
        "semester": "2023-fall",
        "content_score": 5,
        "difficulty_score": 3,
        "gain_score": 4,
        "comment": "老师讲得很好，内容充实，收获很大。"
    }
    resp = requests.post(f"{base_url}/reviews", headers=headers, json=review_data)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    print("✓ 通过\n")

def test_duplicate_review(student_token):
    print("=== 9. 重复提交评价（应该失败） ===")
    headers = {"Authorization": f"Bearer {student_token}"}
    review_data = {
        "student_id": "s001",
        "course_id": "c001",
        "semester": "2023-fall",
        "content_score": 5,
        "difficulty_score": 3,
        "gain_score": 4,
        "comment": "老师讲得很好"
    }
    resp = requests.post(f"{base_url}/reviews", headers=headers, json=review_data)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    assert resp.status_code == 409
    print("✓ 通过\n")

def test_student_reviews(student_token):
    print("=== 10. 学生查看自己的评价 ===")
    headers = {"Authorization": f"Bearer {student_token}"}
    resp = requests.get(f"{base_url}/students/s001/reviews", headers=headers)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"评价数量: {len(result['data']['reviews'])}")
    print(f"评价内容: {json.dumps(result['data']['reviews'], ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    assert len(result["data"]["reviews"]) > 0
    print("✓ 通过\n")

def test_teacher_summary():
    print("=== 11. 教师查看课程汇总 ===")
    from app.services.auth_service import generate_teacher_token
    teacher_token = generate_teacher_token("t001")
    headers = {"Authorization": f"Bearer {teacher_token}"}
    resp = requests.get(f"{base_url}/teachers/t001/courses/c001/summary", headers=headers)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    print("✓ 通过\n")

def test_sensitive_words(token):
    print("=== 12. 测试敏感词过滤 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先设置敏感词
    resp = requests.post(
        f"{base_url}/admin/censor-words",
        headers=headers,
        json={"words": ["很差", "垃圾", "混蛋"]}
    )
    print(f"设置敏感词 - 状态码: {resp.status_code}")
    assert resp.status_code == 200
    
    # 学生提交带敏感词的评价
    from app.services.auth_service import generate_student_token
    student_token = generate_student_token("s002")
    student_headers = {"Authorization": f"Bearer {student_token}"}
    
    review_data = {
        "student_id": "s002",
        "course_id": "c001",
        "semester": "2023-fall",
        "content_score": 1,
        "difficulty_score": 1,
        "gain_score": 1,
        "comment": "这个老师讲课很差，简直是垃圾！"
    }
    resp = requests.post(f"{base_url}/reviews", headers=student_headers, json=review_data)
    print(f"提交带敏感词评价 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    assert result["data"]["sensitiveFlag"] == True
    
    # 管理员查看命中敏感词的评价
    resp = requests.get(
        f"{base_url}/admin/reviews?sensitive=true",
        headers=headers
    )
    print(f"查看敏感评价 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"命中敏感词的评价数: {len(result['data']['reviews'])}")
    if result["data"]["reviews"]:
        review = result["data"]["reviews"][0]
        print(f"过滤后的评语文本: {review['comment']}")
        assert "***" in review["comment"]
    
    print("✓ 通过\n")

def test_semester_close(token):
    print("=== 13. 测试学期结课 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先查看学期列表
    resp = requests.get(f"{base_url}/admin/semesters", headers=headers)
    print(f"学期列表 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"学期: {json.dumps(result['data']['semesters'], ensure_ascii=False, indent=2)}")
    
    # 结课2024-fall学期
    resp = requests.post(
        f"{base_url}/admin/semesters/2024-fall/close",
        headers=headers
    )
    print(f"结课操作 - 状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    assert resp.status_code == 200
    
    # 验证课程状态已更新
    resp = requests.get(f"{base_url}/courses", headers=headers)
    result = resp.json()
    fall_courses = [c for c in result["data"]["courses"] if c["semester"] == "2024-fall"]
    print(f"2024-fall学期课程状态: {fall_courses[0]['status'] if fall_courses else 'N/A'}")
    assert fall_courses[0]["status"] == "closed"
    
    print("✓ 通过\n")

if __name__ == "__main__":
    try:
        test_healthz()
        token = test_admin_login()
        test_courses(token)
        test_students(token)
        test_teachers(token)
        test_admin_stats(token)
        student_token = test_student_available_courses()
        test_submit_review(student_token)
        test_duplicate_review(student_token)
        test_student_reviews(student_token)
        test_teacher_summary()
        test_sensitive_words(token)
        test_semester_close(token)
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
