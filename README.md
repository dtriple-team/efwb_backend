# IoT Health Monitoring Platform

## 개요

...

## 주요 기술 스택

- Backend: Flask, Flask-SQLAlchemy, Flask-MQTT, Flask-SocketIO
- Frontend: Vue.js, Vuetify
- Database: SQLAlchemy ORM
- Real-time Communication: Socket.IO, MQTT

## 프로젝트 구조

```
project/
├── backend/
│   ├── api/
│   │   ├── api_band.py
│   │   ├── api_create.py
│   │   ├── crawling.py
│   │   ├── mqtt.py
│   │   ├── socket.py
│   │   └── thread.py
│   ├── db/
│   │   ├── query/
│   │   │   ├── select.py
│   │   ├── service/
│   │   │   ├── query.py
│   │   │   └── select.py
│   │   ├── __init__.py
│   │   └── database.py
│   ├── server_configuration/
│   │   ├── __init__.py
│   │   └── app.config.py
│   └── __init__.py
├── efwb-frontend/
│   └── App.vue
├── main.py
├── manage.py
└── README.md
├── requirements
```

## 주요 기능

### 1. 사용자 관리

- 로그인, 로그아웃
- 사용자 권한 관리 (permission 레벨)

### 2. 그룹 관리

- 그룹 생성, 수정, 삭제
- 사용자-그룹 연결 관리

### 3. 밴드 (웨어러블 디바이스) 관리

- 밴드 등록, 수정, 삭제
- 사용자-밴드 연결 관리

### 4. 센서 데이터 처리

- MQTT를 통한 실시간 데이터 수신
- 데이터베이스 저장 및 실시간 클라이언트 통지
- 걸음 수, 심박수, 산소포화도 등 다양한 생체 정보 처리

### 5. 데이터 분석 및 시각화

- 일별, 기간별 센서 데이터 집계 및 조회
- 차트 데이터 생성 (프론트엔드에서 시각화)

### 6. 이벤트 관리

- 낙상 감지, 배터리 부족 등 다양한 이벤트 처리
- 이벤트 로깅 및 알림

### 7. 실시간 모니터링

- SocketIO를 통한 실시간 데이터 및 이벤트 전송
- 클라이언트에 실시간 업데이트 제공

### 8. 백그라운드 작업


### 9. 보안

- 토큰 기반 인증
- API 엔드포인트 접근 제어

### 10. 기타

- 날씨 정보 조회

## 파일별 주요 기능

### App.vue

- Vue.js 기반의 프론트엔드 메인 컴포넌트
- 네비게이션 드로어, 앱 바, 라우터 뷰 등 기본 레이아웃 구성
- 사용자 인증 상태에 따른 조건부 렌더링
- 반응형 디자인 구현 (Vuetify 사용)

### **init**.py

- Flask 애플리케이션 초기화 및 설정
- 데이터베이스, 로그인 매니저, API 매니저, SocketIO, MQTT 클라이언트 초기화
- 라우트 설정 (메인 페이지, 밴드, 게이트웨이, 사용자, 로그 등)

### database.py

- DBManager 클래스 정의: 데이터베이스 초기화 및 관리
- 더미 데이터 삽입 메서드 구현
- 비밀번호 암호화 함수
- 날짜, IP 주소 등 유틸리티 함수 구현

### api_band.py

- RESTful API 엔드포인트 구현
- 사용자 인증 (로그인, 로그아웃)
- 그룹, 사용자, 밴드, 게이트웨이 관련 CRUD 작업
- 센서 데이터 조회 및 분석 API
- 이벤트 로그 관리
- 날씨 정보 조회
- 신경 자극 처방 관리

### api_create.py

- Flask-Restless를 사용한 자동 API 생성
- 각 모델에 대한 CRUD API 엔드포인트 생성
- API 접근에 대한 토큰 인증 전처리기 설정

### mqtt.py

- MQTT 메시지 핸들링
- 동기 및 비동기 데이터 처리
- 게이트웨이 상태 관리
- 수신된 센서 데이터의 데이터베이스 저장 및 실시간 클라이언트 통지

### socket.py

- SocketIO 이벤트 핸들러 구현
- 클라이언트 연결/연결 해제 관리
- 실시간 이벤트 발송 기능

### thread.py

- 백그라운드 작업 스레드 구현

