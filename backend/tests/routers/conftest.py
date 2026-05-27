"""
라우터 계층 pytest 픽스처 모음.

tests/routers/ 하위 테스트 파일에서 사용되는 픽스처.
현재 라우터 테스트는 순수 함수(_to_analyze_response, _validate_file 등)만
검증하므로 TestClient 픽스처가 필요 없다.

F008(공유 링크), F011(분석 기록 조회) 구현 시 아래 패턴으로 추가한다:

    @pytest.fixture
    def client(monkeypatch):
        from fastapi.testclient import TestClient
        from main import app
        from core.auth import verify_token
        app.dependency_overrides[verify_token] = lambda: {'sub': 'test-user-id'}
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()
"""
