# 외부 구성 요소와 고정 입력

- StarCraft / StarCraft Remastered: Blizzard Entertainment. 원본 캠페인 CHK, DAT, 지형 입력을 모드 변환과 검사에 사용합니다. 이 저장소와 배포본은 별도의 게임 설치를 필요로 합니다.
- SAMASE64 0.10.28: Neiv, BoneHorror/Nekron 배포본. 출처·커밋·다운로드 주소·바이너리 SHA-256은 `sc1/native_campaign/loader_pin.json`에 있습니다. 네이티브 플러그인의 API44 C ABI 적응은 각 헤더에 출처를 기록했습니다.
- Tatti3: `neivv/tatti3`, 커밋 `eb940dab410e9e197db9634322e91fb67a0b7f0f`. 필요한 DAT 참조 코드와 고정 출력만 보관합니다. 파일별 출처와 해시는 `sc1/native_campaign/dat_sources/tatti3/source_pin.json`, `support_dat_sources/headless/upstream_pin.json`을 참고하세요.
- CPython 3.11.8, Tcl/Tk, OpenSSL: 실행기 ZIP에 포함합니다. Python 라이선스는 ZIP의 `licenses/Python-LICENSE.txt`, Tcl/Tk 라이선스는 `runtime/tcl`, OpenSSL 고지는 `licenses`에 포함합니다. 소스 저장소에는 Python 가상 환경을 포함하지 않습니다.

각 외부 구성 요소의 기존 권리와 조건은 해당 구성 요소에 적용됩니다.

초기 EUD 시제품과 개발 도구:

- [eudplib](https://github.com/armoha/eudplib), [원래 eudplib](https://github.com/phu54321/eudplib), [euddraft](https://github.com/armoha/euddraft): 초기 EUD 지도 실험에 사용했습니다. 현재 배포판의 실행 경로는 Python 관리자와 SAMASE 네이티브 플러그인입니다.
- [CascLib](https://github.com/ladislav-zezula/CascLib): 설치된 게임 자료를 읽기 전용으로 추출하는 데 사용했습니다.
- [Pillow](https://github.com/python-pillow/Pillow), [PyMS](https://github.com/poiuyqwert/PyMS): 지도 미리보기 이미지 처리와 지형·스프라이트 형식 참고에 사용했습니다.
