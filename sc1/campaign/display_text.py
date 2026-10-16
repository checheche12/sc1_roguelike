"""Concise player-facing summaries; source text and saved records stay untouched."""
from __future__ import annotations

_SUMMARIES = {
    "b0b87a48-4e2f-4d83-b1e9-d31ab203442a": "아군 마린 사거리 +1",
    "9da04c9f-9ddd-4e51-8333-e40eb7fafd1a": "아군 마린 최대체력 +10",
    "11add15f-8880-4db0-9697-91723ffdfd57": "아군 마린 공격속도 30% 증가",
    "b4a56885-dcef-4fd7-9b1d-1d07fa0cbd5c": "아군 파이어뱃 최대체력 100으로 변경",
    "3de768b5-3b1c-4aa2-a80f-fa72d5e37a73": "아군 고스트 최대체력 +30",
    "61ca33c4-6b46-45fd-bf48-36e92fc30067": "아군 고스트 공격 유형을 일반형으로 변경",
    "bec5aa24-1479-4c55-9de9-ddb843ddc039": "아군 벌쳐 공격 주기 20% 감소",
    "e52e8e8a-090c-48dd-80d2-03142775c1d4": "아군 벌쳐 광물 50·인구 1·최대체력 50으로 변경",
    "8b6431dd-5553-4743-a43f-ef61172b46f6": "아군 시즈탱크 탱크 모드 사거리 +1",
    "fde47c79-594b-4731-9669-0df4044da1f4": "아군 시즈탱크 시즈 모드 사거리 +2",
    "911cc0df-8191-49ff-a058-8390ce15e910": "아군 골리앗 최대체력 +20",
    "adcf3a4f-948d-4c2e-b184-e48544c7afcf": "아군 레이스 지상·공중 사거리 +2",
    "61c98944-9414-47f2-bcdf-6d4ff0ba5598": "아군 레이스 최대체력 +30",
    "31e8e8c8-347d-456b-bd0d-cae47f591eb8": "아군 발키리 공격 주기 20% 감소",
    "e4565c77-cc6f-43ea-91ee-1448e52cc757": "아군 배틀크루저 지상·공중 사거리 +2",
    "676ab7d6-96fb-5748-8796-d8570dc554e6": "아군 SCV·드론·프로브 생산 시간 50% 감소",
    "7bd974f2-42ce-5442-b22f-6e82fcb8fe51": "아군 SCV·드론·프로브 최대체력 +20",
    "0f78b098-5745-47de-b9cb-c74e3beb411f": "아군 골리앗 이동속도 20% 증가",
    "dc005b01-501a-4861-9d56-b971125e134a": "아군 레이스 이동속도 20% 증가",
    "08dc86c3-0018-43d7-a1ca-092a863bf4dd": "아군 드롭십 이동속도 100% 증가",
    "af9ac5eb-ba74-4fe5-b3bf-b9e69a3a87f4": "아군 배틀크루저 이동속도 50% 증가",
    "4e6aec23-a4ae-587b-b726-a1bc3b99de85": "아군 파이어뱃 방어력 +1",
    "d417aff9-333a-5843-895f-3d38c611f470": "아군 파이어뱃 화염 타격당 공격력 +2",
    "6d59aecf-b1a8-50e1-b33f-8fba3bc851a0": "아군 메딕 최대체력 +20",
    "4b4ddc45-9884-5bf3-8063-ad76c6d43495": "아군 메딕 이동속도 15% 증가",
    "ff284e41-e8d7-53dd-946a-de2807c134dd": "아군 골리앗 지상 공격력 +3",
    "f4828e4e-8b66-5d82-96fe-02763018b98f": "아군 골리앗 방어력 +1",
    "31325774-f8b6-5124-b076-05c2e94f0555": "아군 드롭십 최대체력 +40",
    "5494c103-af5a-59a2-bb3e-491784fa4a32": "아군 발키리 최대체력 +40",
    "220b33e4-9460-5610-b765-86c536482a8d": "아군 사이언스 베슬 최대체력 +40",
    "9316f1ce-9294-54ea-b4e4-812d1c75dfba": "아군 발키리 공중 사거리 +1",
    "d6f25615-a491-5eee-87fd-73031e4a18b2": "아군 드롭십 수송 공간 +4칸",
    "02639414-0de5-5a1d-afdc-04e3fe871032": "아군 발키리 미사일 폭발 반경 20% 증가",
    "f6286deb-00ba-5ade-bade-5f51b4f22e7b": "아군 사이언스 베슬 시야·탐지 범위 +2",
    "a6948251-7b11-51ce-899d-0816edd0995a": "아군 저글링 최대체력 +10",
    "ef8ab539-27b9-50d7-8334-ab5f9c8d9a5f": "아군 저글링 공격 주기 20% 감소",
    "50397b65-4a2d-537f-9f37-cc535b98cde4": "아군 히드라리스크 지상·공중 사거리 +1",
    "10a554d6-3258-50f2-bcce-f0cc05a5a21c": "아군 히드라리스크 최대체력 +20",
    "19e4b7ea-bd4b-5e25-a362-6379770f253e": "아군 러커 사거리·일직선 가시 도달 거리 +1",
    "bcc8fdd9-aa12-55c0-a747-7bfb3ba0df69": "아군 울트라리스크 최대체력 +100",
    "62773fb3-a08d-5eea-a5f8-afc4fa240491": "아군 울트라리스크 방어력 +2",
    "474028ba-4784-5ea6-a4d6-5be6025d4289": "아군 뮤탈리스크 최대체력 +20",
    "937deca5-e0df-518a-9db5-738801a7d78a": "아군 가디언 지상 사거리 +1",
    "5323e004-5669-5f9b-b74f-eb4feb45c0bd": "아군 디바우러 최대체력 +50",
    "88179125-fb11-56f7-a6e5-fdbe01513202": "아군 디바우러 공격 주기 25% 감소",
    "70868f85-8196-5c56-b775-4b247f32bf3a": "아군 스커지 이동속도 25% 증가",
    "8453bd7a-0f86-5415-b26b-e3dcafab73d8": "아군 스커지 자폭 공격력 25% 증가",
    "a1fbb3c9-68f7-5b77-a131-9415ba633222": "아군 오버로드 최대체력 +50",
    "4c71f828-2be8-5786-8902-c45333a38e40": "아군 인페스티드 테란 이동속도 30% 증가",
    "51941deb-1b6b-50b6-a8b8-b25bd1fb43c7": "아군 저글링 공격력 +1",
    "08063950-39d5-5e62-8488-d5226f097db1": "아군 저글링 방어력 +1",
    "7c993c03-1411-5c14-9661-51056fca369d": "아군 히드라리스크 지상·공중 공격력 +2",
    "50938e75-f810-50e5-9755-2b624f55a663": "아군 히드라리스크 이동속도 15% 증가",
    "1ef2e74d-c3fb-5667-bf75-0695ec30f019": "아군 러커 최대체력 +30",
    "a78ec969-f1e0-5b81-be72-2c100c1cb6c8": "아군 러커 공격력 +4",
    "55cb0c50-2498-5194-ad1e-935baf84b110": "아군 울트라리스크 이동속도 15% 증가",
    "807cc622-fda9-5ceb-a96a-3457b0074753": "아군 울트라리스크 알 부화 시간 20% 감소",
    "fec86599-89dc-5015-afab-a207e9258707": "아군 뮤탈리스크 방어력 +1",
    "2e8b32df-a697-5eaf-85b1-eb0999c0754e": "아군 뮤탈리스크 첫 공격력 +2 (튕김 피해에도 반영)",
    "bc1c87d6-a946-5e55-a727-db572294557c": "아군 가디언 최대체력 +30",
    "7651ad59-5052-56c1-85fe-74133ad7660e": "아군 가디언 이동속도 25% 증가",
    "93d79797-e57b-52c1-8a79-4f75774fb40d": "아군 디바우러 방어력 +1",
    "8deedc39-6d94-5ecf-b7d2-1ef08292a610": "아군 스커지 최대체력 +10",
    "df095ca0-42a6-5230-b976-4a8f6588db92": "아군 여왕 최대체력 +30",
    "25652a52-018d-5c53-9f56-9b0f2a8e1cef": "아군 디파일러 최대체력 +25",
    "793931fa-f87a-5a0f-a575-bff6bcce6a5d": "아군 오버로드 알 부화 시간 25% 감소",
    "c1855946-9678-5a02-83a6-4c30e6011f17": "아군 인페스티드 테란 최대체력 +30",
    "6e4f04ef-f498-5852-b175-cc46b156c4fc": "아군 가디언 공격 주기 20% 감소",
    "58810cf9-1b79-5226-8734-f11735a024e0": "아군 인페스티드 테란 자폭 반경 15% 증가",
    "6133f55d-779f-567a-94ad-6f354e50cd41": "아군 질럿 최대보호막 +20",
    "d8b24b05-1222-5d5f-95ab-2888640519b4": "아군 질럿 공격 주기 20% 감소",
    "6be08978-7d28-5f6d-a9ee-621e4f6b236c": "아군 드라군 최대체력 +20",
    "15752ea5-1048-5307-b4d6-89e1f92376c1": "아군 드라군 지상·공중 사거리 +1",
    "8a5dc9f5-bb51-5c09-8f7f-12890b39a04f": "아군 다크 템플러 이동속도 20% 증가",
    "bc13f025-ec31-53d6-bb9b-3b378f8b7d9e": "아군 아콘 최대보호막 +100",
    "a45b1173-35e7-5c3d-957a-7d1483a281fa": "아군 아콘 지상·공중 사거리 +1",
    "25930078-74c8-5c75-8ad2-44ebefb8db05": "아군 셔틀 이동속도 40% 증가",
    "26ef37d2-4048-5abd-aba5-7c9e510361cc": "아군 셔틀 수송 공간 +4칸",
    "60f86c7c-f4f0-5a0a-8b81-94dee26bc64b": "아군 리버 최대체력 +40",
    "91425e65-1f04-5ea4-a848-59e2c2c7f39b": "아군 스캐럽 생산 시간 30% 감소",
    "5792be66-e81b-5b2d-b908-a7819f4fcf33": "아군 옵저버 이동속도 30% 증가",
    "e12772d8-620e-5550-b33f-000515770bec": "아군 옵저버 시야·탐지 범위 +2",
    "35005b20-4108-57d7-ac38-5c468f0482e5": "아군 스카우트 지상 공격력 +8",
    "dc0cd4aa-13b0-5fa9-aa16-e049aa803700": "아군 스카우트 이동속도 25% 증가",
    "b183e8bf-f97d-57e9-b3bd-e2baaebeb92f": "아군 인터셉터 생산 시간 30% 감소",
    "692a2bd1-5537-568c-b6b5-75e1317b1a4d": "아군 질럿 최대체력 +20",
    "0c4c4678-5be2-5f3b-8eb0-dddb701c121b": "아군 질럿 체력 방어력 +1",
    "55808e0e-ea2d-57a3-a2c7-2554e8fa55be": "아군 드라군 최대보호막 +30",
    "935452ab-4e90-5aab-9c90-eb9cc55ed087": "아군 드라군 지상·공중 공격력 +3",
    "d763e2fb-431a-50ba-bfc7-de9279922b42": "아군 하이 템플러 최대체력 +20",
    "daa8e37c-7b5a-576c-9ba9-ce97b724dedf": "아군 하이 템플러 이동속도 20% 증가",
    "06f4d7f5-202f-51cb-a81d-1ef2aa8bc78e": "아군 다크 템플러 최대체력 +20",
    "82e789b7-6fa9-5ced-af07-d966b5749d39": "아군 다크 템플러 최대보호막 +30",
    "e34227bb-1234-5802-899f-a7ff46a4f649": "아군 다크 아콘 최대보호막 +50",
    "fe5b3fad-5ebc-5573-8296-a9d91b138c22": "아군 셔틀 최대체력 +40",
    "4fedad7f-2fb9-504e-9454-c768e09d905c": "아군 리버 체력 방어력 +1",
    "2c49c57a-0bb8-5bc4-a725-e61e966fc586": "아군 옵저버 최대보호막 +20",
    "02b80d02-b3d1-59a1-bd16-f8a31dc292ea": "아군 스카우트 최대보호막 +40",
    "8ca6d74c-c10f-537b-98e3-8d2a6583f046": "아군 커세어 체력 방어력 +1",
    "a81b8e17-c7f6-507f-8474-5c35a2d9116d": "아군 캐리어 최대체력 +60",
    "dbf5c3bc-dcba-5215-b5dd-e713baa4fe73": "아군 아비터 최대체력 +40",
    "40e316b0-df99-5b23-b712-60b863f6fd19": "아군 스카우트 지상·공중 사거리 +1",
    "461b08f1-9cc2-5373-a555-65779ae7e14c": "아군 커세어 공중 사거리 +1",
    "57102deb-c97b-57d0-ba5c-43cce2d4305d": "아군 인터셉터 최대체력·최대보호막 각각 +20",
    "481876a7-e041-567c-91c0-dbbe5915acaf": "적 추가 공세 병력, 중첩당 기본 편성의 25% 증가",
    "639d3bf8-b455-5b0d-9954-7695a39eb0e5": "적 일반 공격 피해, 중첩당 7.5% 증가",
    "8704b857-aed8-5888-aac3-bada4065990d": "적 전투 유닛 최대체력, 중첩당 10% 증가",
    "163a6ce5-eefc-59eb-9e79-840ff9a96dab": "적 공격속도·이동속도, 중첩당 7.5% 증가",
    "fada488d-f5bb-56ab-8744-96fc84f761f9": "적 추가 공세 빈도, 중첩당 10% 증가 (첫 공세 그대로·최소 간격 45초)",
    "d7c5e877-1599-5720-9279-641bb9665846": "적 추가 공세 병력: 6초간 미피격 시 초당 최대체력 1% 회복/중첩",
    "ed0bf3fc-1207-5661-b747-ad4b93d00801": "기존 적 20기 처치마다 기지 지원군 8인구 (추가 중첩 +4·재사용 60초)",
    "edcac92f-f130-5127-823a-444835d88df4": "적 추가 공세에 중첩당 정예 1기: 최대체력 +50%·일반 공격 +20%",
    "4d0ba81b-2aa6-5c27-afe1-b5cf18f32635": "적 추가 공세 선두 4기(추가 중첩 +2): 20초간 일반 피해 25% 감소",
    "627eb6b5-6ffd-53f8-ad40-6f47334b67ed": "적이 8초간 공격·피격 없으면 다음 일반 공격 피해 +20/30/40%",
    "8ebeaec8-a158-5106-872f-15076ff01781": "적 추가 공세 처치 1초 뒤 반경 0.75 폭발: 아군 지상 전투병에게 방어 무시 8/12/16 피해",
    "af31dc50-9617-5f01-8301-fd5913531f91": "적 일반 공격으로 준 체력 피해의 10% 회복/중첩",
    "e8099fe1-cac1-5c0d-bffc-1d41e9b54959": "적 공세 구호반 1/2/3기: 반경 3의 동료 1기에게 초당 체력 6 회복",
    "9b03167c-e96a-5726-a710-0787e8d406af": "적 공세 지휘관 사망 시 반경 6의 8/12/16기: 8초간 일반 공격 +25%·이동속도 +20%",
    "2743de38-d9b0-5006-b1e6-a8f4b258d12f": "적 공세 1/2/3쌍: 짝 사망 2초 뒤 생존자 최대체력의 35%를 1회 회복",
    "5e871f9a-f71b-475b-82a1-0879d54d9d30": "아군 골리앗 지상 1기·공중 1기 동시 공격 (독립 주기)",
    "f08eec6e-b40c-4b25-8fb2-cd5710d54401": "아군 배틀크루저 최대 3대상 동시 공격 (원래 피해)"
}
def concise_description(item: dict) -> str:
    """Render current/legacy canonical items without mutating their pinned record."""
    if item.get('rework_revision')==5 or item.get('effect',{}).get('qa_revision'):
        return str(item.get('description') or '').strip()
    if item.get('offer_family'):
        return str(item.get('description') or '').strip()
    if summary := _SUMMARIES.get(item.get("id")):
        return summary
    text = str(item.get("source_description") or item.get("description") or "").strip()
    target = str(item.get("target") or "").strip()
    return f"{target}: {text}" if target and target not in text else text

def apply_display_descriptions(catalog: dict) -> None:
    for group in ("talents", "curses"):
        for item in catalog[group]:
            item["description"] = concise_description(item)


def current_owned_descriptions(status: dict, catalog_path=None) -> dict:
    """Project current compatible descriptions without rewriting saved choices."""
    if status.get('catalog_version') not in (1,2) or not (status.get('talents') or status.get('curses')):
        return status
    import copy
    from .runtime_catalog import load_catalog
    current=load_catalog(catalog_path,expected_version=status['catalog_version'] if catalog_path else 2)
    result=dict(status)
    for kind,index in (('talents','bit_index'),('curses','byte_index')):
        latest={item['id']:item for item in current[kind]}
        result[kind]=[]
        for saved in status[kind]:
            item=copy.deepcopy(saved);new=latest.get(item['id'])
            if (new is not None and new[index]==item[index]
                    and new.get('source_description')==item.get('source_description')
                    and new.get('effect',{}).get('qa_revision',0)>=item.get('effect',{}).get('qa_revision',0)):
                item.update(description=new['description'],effect=copy.deepcopy(new['effect']))
            result[kind].append(item)
    return result
