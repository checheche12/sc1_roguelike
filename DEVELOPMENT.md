# 개발과 빌드

필수 환경: Windows x64, **CPython 3.11.8 x64(Tcl/Tk 포함)**, Visual Studio C++ Desktop 빌드 도구와 Windows SDK입니다. 빌드 도구는 `vswhere`로 찾고 `vcvars64.bat` 환경을 읽습니다. 개인 PC의 컴파일러 경로나 환경 파일은 필요하지 않습니다.

저장소 루트에서 실행합니다. 아래 `python`은 3.11.8을 가리켜야 합니다.

```powershell
python -B -X utf8 -m unittest sc1.tests.test_rework_growth sc1.tests.test_talent_campaign_policy sc1.tests.test_timed_survival_victory sc1.tests.test_resource_layout sc1.tests.test_ladder_resource_layout
python -B -X utf8 sc1/build_release.py --output sc1/dist/SC1_Roguelike_local --receipt sc1/dist/build_result.json
```

두 번째 명령은 기본 T01 입력, 전체 63개 지도, 네이티브 DLL, 패키지, 실행기와 ZIP을 차례로 만듭니다. 네이티브 프로덕션 호스트 검사, 선택 UI 검사, Python/네이티브 프로토콜 검사를 통과해야 패키징하며, 마지막에 실행기 자체 검사와 ZIP 전체 SHA-256 대조를 수행합니다. 출력 폴더와 ZIP 이름은 아직 존재하지 않는 경로를 지정하세요. 게임 실행·설치와 사용자 기록 변경은 수행하지 않습니다.

전체 지도 공세의 원래 배치 유닛까지 포함한 추가 모의 검사는 지도 빌드 후 실행합니다.

```powershell
python -B -X utf8 sc1/native_campaign/verify_wave_occupancy.py
```

이 검사는 실제 엔진 실행이 아닌 합성 콜백 검사입니다. 생산 기지를 나중에 확보하는 지도는 정상 경제 확보 상태를 만들어 공세 생성을 검사합니다.

이미 봉인한 패키지에서 실행기와 ZIP만 만들려면 다음과 같이 실행합니다.

```powershell
python -B -X utf8 sc1/build_release.py --manifest sc1/native_campaign/builds/<빌드명>/manifest.json --output sc1/dist/SC1_Roguelike_local2
```

## 파일 위치

| 위치 | 용도 |
| --- | --- |
| `sc1/campaign`, `sc1/manager`, `sc1/bridge` | 성장·기록·관리자·연결 프로토콜 |
| `sc1/native_campaign/plugin` | 실제 게임 네이티브 효과 및 호스트 검사 |
| `sc1/native_campaign/*layout*.py` | 광물·가스 배치 및 경로 검사 |
| `sc1/native_campaign/build_*.py`, `package_*.py` | 지도·DLL·검증된 패키지 생성 |
| `sc1/build_portable.py`, `portable_launcher.cpp`, `portable_runtime.py` | 독립 실행기 및 묶음 Python 런타임 |
| `sc1/campaign_sources/raw` | 고정된 원본 지도·DAT·지형 입력 |
| `sc1/native_campaign/managed_dat`, `support_dat`, `all_requirements` | 검증된 DAT 파생 입력 및 출처 증거 |
| `sc1/native_campaign/dat_sources`, `support_dat_sources` | 고정된 DAT 참조 코드·출력 |
| `analysis/runtime_rework_20261016` | 확정 설계 사본과 표시 문구 입력 |
| `sc1/tests` | Python 회귀 검사 |

기본 빌드는 저장된 카탈로그와 생성 헤더를 사용합니다. 카탈로그 설계를 바꿀 때는 `sc1/campaign/build_rework_catalog.py` 및 `generate_native_catalog.py`를 함께 확인하세요. 레거시 ID·비트 위치는 이미 발행된 기록과의 호환 규약입니다. 확정 입력 사본을 실시간 편집 파일로 사용하지 마세요.

빌드 영수증에는 그 빌드의 절대 경로와 SHA-256이 포함됩니다. 다른 경로로 소스를 옮기면 지도·DLL·패키지를 다시 생성해야 합니다. 생성 결과는 `.gitignore`에 따라 커밋하지 않습니다. 배포 ZIP은 불변 Git 산출물 태그(`asset-v…`)에 올리고 README의 직접 다운로드 링크를 갱신합니다. 소스 버전 태그(`v…`)와 구별합니다.

고정 입력의 출처 해시는 줄바꿈 바이트까지 포함하므로 `.gitattributes`에서 자동 줄바꿈 변환을 끕니다.

## 적 업그레이드와 마법

`enemy_progression.h`는 게임 시뮬레이션 프레임을 누적하며 선택창·연결 대기·목표 완료 중에는 멈춥니다. 6·8·10·12·14·16분의 테크 단계는 README에 적혀 있습니다. 공방·보호막은 6·10·14분에 최소 1·2·3으로 올리고 기존 레벨을 낮추지 않습니다. 적 소유자만 갱신하며, 다른 종족의 추가 병력을 같은 소유자가 운용할 수 있어 세 종족의 표준 업그레이드를 함께 준비합니다. SAMASE의 확장 배열 0(업그레이드)·2(연구)를 우선하고, 배열이 없을 때만 레거시 Game 배열을 사용합니다. 기존 병력과 나중에 생성된 병력의 이동·공속 플래그도 갱신합니다.

탐지 대군주의 추가 공세 전용 속도 하한은 1707/256픽셀/프레임이며 인스네어 중에는 절반입니다. 원래 이동 속도는 별도로 보존해 소유권 이전 때 복구합니다. 적 전체의 일반 대군주 속업은 8분 단계입니다.

`enemy_spell_runtime.h`는 추가 공세의 신원 표시가 유효한 유닛만 제어합니다. 기존 임무 AI·영웅 명령은 제어하지 않습니다. 연구·에너지·시야·탐지·유효 대상·자기 병력 피해·중복 예약을 확인한 뒤 공개 API `CheckTechTargeting`으로 엔진의 최종 대상 규칙을 확인합니다. 실제 에너지 지출과 효과는 네이티브 시전 명령이 처리합니다. 연구 해금만으로 원래 AI가 모든 마법을 사용한다고 보장하지는 않습니다.

회귀 검사는 프로덕션 DLL과 같은 번역 단위에서 경계 시각, 기존 고레벨 유지, 소유자 격리, 확장 배열 범위, 속도와 상태 이상, 신규 생성, 소유권 이전, 마법 역할·연구·시야·에너지·엔진 대상 거부·광역 중복/아군 피해를 검사합니다. 합성 콜백 검사이며 실제 게임 내 시전 외관과 전투 난이도는 별도 플레이 QA가 필요합니다.

## 일반 교범의 임시 추첨 가중치

새 PHC1 v2 재능 선택지를 발행할 때 같은 캠페인에서 이미 표시된 최근 재능 보상 3회의 `candidates_json`을 읽습니다. 선택하지 않은 일반 반복 교범도 포함합니다. 최근에 나온 교범의 같은 등급 내 추첨 가중치는 95, 나머지는 100이며, 기본 등급 확률과 무한 중첩 효과는 그대로입니다. 정규화된 개별 카드의 최종 확률을 5%포인트 빼는 방식은 아닙니다. 후보 전부가 같은 가중치이면 기존의 균등 추첨을 유지합니다.

재등장은 기간만 갱신하며 감소율을 누적하지 않습니다. 경제·전설 보상도 재능 보상 1회로 세고, 저주·연결 재시도·미발행 보상은 세지 않습니다. 다른 캠페인 기록은 섞지 않습니다. 기존 선택지와 스냅샷은 다시 추첨하거나 덮어쓰지 않으며 추가 DB 마이그레이션이 필요 없습니다. `test_manual_offer_cooldown.py`와 `test_rework_growth.py`에서 가중치 경계·만료·재등장·미선택·재접속을 검사합니다.

## QA2 마법 대상 검사 크래시 수정

2026-10-16 17:27:42 사용자 덤프에서 네이티브 `CheckTechTargeting`의 방어막 검사(기술 6)가 잘린 대상 주소를 사용했습니다. 로더 0.10.28의 `hook_func` 구현과 덤프의 호출 인자를 대조하니 Func24의 세 번째 인자 마스크가 `0xffff`였습니다. 64비트 대상 주소의 하위 16비트만 전달된 뒤 유닛 플래그를 읽으며 접근 위반이 발생했습니다.

대상 포인터를 유지하는 Func25 `CheckOrderTargeting` 훅으로 교체했습니다. 유기체 락다운과 퀸 감염 재능의 대상 조건 및 원상 복구를 이 경로에서 유지합니다. 추가 공세의 마법 사전 검사는 훅을 등록하지 않은 Func24의 직접 조회 함수를 사용합니다. SAMASE나 게임 실행 파일을 수정하지 않습니다.

`targeting_bridge_host_tests.h`는 실제 로더의 x64 디스패처 바이트를 실행하여 주소 손실을 재현하고, 전체 포인터 전달과 Func24 미등록을 확인합니다. 일반 적 사이언스 베슬의 방어막 대상 전달도 검사합니다. 이는 덤프·바이너리 분석 및 합성 실행 검사이며, 수정 후 실제 게임에서의 재발 검증은 별도입니다. 사용자 덤프와 세션 로그는 공개 저장소에 올리지 않습니다.
