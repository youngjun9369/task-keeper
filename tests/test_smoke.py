def test_create_and_list(client):
    res = client.post("/tasks", json={"title": "테스트 할 일", "tags": ["개인", "긴급"]})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "테스트 할 일"
    assert {t["name"] for t in body["tags"]} == {"개인", "긴급"}

    res = client.get("/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["tags"]


def test_list_tasks_query_count_is_constant(client, db_session):
    # 할 일 개수와 상관없이 GET /tasks 쿼리 수가 일정해야 합니다(N+1 회귀 방지).
    from sqlalchemy import event

    for i in range(10):
        client.post("/tasks", json={"title": f"할 일 {i}", "tags": [f"태그{i}"]})
    db_session.expire_all()

    engine = db_session.get_bind()
    count = 0

    def _count(*_):
        nonlocal count
        count += 1

    event.listen(engine, "before_cursor_execute", _count)
    try:
        res = client.get("/tasks")
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    assert res.status_code == 200
    assert len(res.json()) == 10
    assert count <= 2
