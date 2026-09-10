# wmux 연동 설정법 (OpenCode)

> 검증 환경: Windows 11 + wmux 0.7.10 + opencode 1.18.30. `MCP 서버 설치`는 불필요 —
> wmux는 MCP가 아니라 **OpenCode 플러그인(`wmux.js`) + CLI**로 에이전트를 인식한다.

## 1. 플러그인 설치

wmux에 번들된 플러그인을 전역 플러그인 폴더에 복사한다.

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.config\opencode\plugins" -Force
Copy-Item "$env:LOCALAPPDATA\Programs\wmux\resources\opencode-plugin\wmux.js" `
  -Destination "$env:USERPROFILE\.config\opencode\plugins\wmux.js" -Force
```

무결성/문법 확인 후 **opencode 재시작** (wmux 자체 재시작은 불필요):

```powershell
(Get-FileHash "$env:LOCALAPPDATA\Programs\wmux\resources\opencode-plugin\wmux.js").Hash -eq `
(Get-FileHash "$env:USERPROFILE\.config\opencode\plugins\wmux.js").Hash
& "C:\Program Files\nodejs\node.exe" --check "$env:USERPROFILE\.config\opencode\plugins\wmux.js"
```

동작: tool 실행/이벤트를 가로채 wmux 사이드바에 보고 (작업중/대기중/완료).
wmux 밖에서는 no-op. 새 tool을 추가하지는 않는다.

## 2. 동작 확인

```powershell
$W = "$env:LOCALAPPDATA\Programs\wmux\resources\cli-bin-ps\wmux.ps1"
& $W ping                                    # pong
& $W report-agent --run-start                 # pane을 working으로 등록
& $W agent-state                              # states에 자식 pane 표시되면 성공
& $W report-agent --run-end                   # 테스트 흔적 정리
```

- 평소 tool 활동은 `agent-activity`로만 보고되어 roster에 상시 뜨지 않는 게 정상.
- 질문/권한 요청 시 자동으로 `blocked` 등록 → 답변 후 해제된다.

## 3. 크로스-pane 메시지

```powershell
$W = "$env:LOCALAPPDATA\Programs\wmux\resources\cli-bin-ps\wmux.ps1"
& $W list-surfaces                             # 상대 pane의 surface id 확인
& $W read-screen --surface <id> --lines 12     # 입력 대기(⊙) 확인
& $W send --surface <id> "메시지"               # 입력
& $W send-key enter --surface <id>             # 전송 (순서 주의: key가 먼저)
```

완료 확인은 같은 turn 안에서 `read-screen` 폴링 (`esc interrupt` 사라지고 답이 보이면 완료).

## 4. 비동기 시그널 규약

- 완료: 상대가 `wmux notify "DONE: 한줄 요약"` + 결과는 `.wmux-inbox/<주제>.md`
- 확인: `wmux list-notifications` (미확인) + inbox 파일 읽기
- 차단: `report-agent --blocked 사유` ↔ `answer-agent --surface <id> --choice <id>`

## 5. 디버깅

```powershell
$env:WMUX_PLUGIN_DEBUG=1   # 이 pane에서 실행한 opencode에만 적용, 영구 저장 아님
opencode
# 로그: $env:TEMP\wmux-plugin-debug.log  (init / cli / tool / event 라인)
Remove-Item Env:WMUX_PLUGIN_DEBUG -ErrorAction SilentlyContinue  # 끄기 (재시작 필요)
```

디버그 판단 기준: 재시작 후 로그에 새 `init` 라인이 없으면 플러그인 미로드.
`init: inactive`면 `WMUX`/`WMUX_SURFACE_ID` 미상속 — wmux pane에서 실행했는지 확인.

## 6. 겪었던 함정

| 증상 | 원인 | 해결 |
|---|---|---|
| 재시작해도 `agent-state` 비어 있음 | `~/.config/opencode/plugin/`(단수)에 설치 | 공식 경로 `plugins/`(복수) 사용. skills.sh 검색 결과의 wmux 스킬(16 installs)은 불필요 |
| `send-key --surface <id> Enter` 실패 | 인자 순서 | `send-key enter --surface <id>` (key 먼저) |
| 디버그 로그 계속 쌓임 | `WMUX_PLUGIN_DEBUG`가 서버 프로세스 메모리에 상주 | 외부에서 제거 불가. 변수 지운 pane에서 opencode 재시작 |
