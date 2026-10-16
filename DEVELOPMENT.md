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

빌드 영수증에는 그 빌드의 절대 경로와 SHA-256이 포함됩니다. 다른 경로로 소스를 옮기면 지도·DLL·패키지를 다시 생성해야 합니다. 생성 결과는 `.gitignore`에 따라 커밋하지 않습니다. 배포 ZIP은 GitHub Release 자산으로 올립니다.

고정 입력의 출처 해시는 줄바꿈 바이트까지 포함하므로 `.gitattributes`에서 자동 줄바꿈 변환을 끕니다.
