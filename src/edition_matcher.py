from datetime import datetime
import re

EDITION = re.compile(r"deluxe|gold|ultimate|complete|definitive|collector|racing fan|edition|에디션|특별판|번들", re.I)


def compare_editions(base, packages, max_age_seconds=600):
    """Name is only a candidate hint; app membership proves the relationship."""
    confirmed, unverified = [], []
    baselines = [p for p in packages if p.kind == "sub" and p.app_ids == [base.id]
                 and not EDITION.search(p.name)
                 and p.composition_verified and p.unconditional
                 and p.currency == "KRW" and p.country == "KR" and p.price is not None
                 and p.scan_id == base.scan_id and p.scan_id
                 and abs((datetime.fromisoformat(p.collected_at) - datetime.fromisoformat(base.collected_at)).total_seconds()) <= max_age_seconds]
    standard = min(baselines, key=lambda p: p.price) if baselines else None
    for p in packages:
        if p.kind not in ("sub", "bundle") or (standard and p.id == standard.id and p.kind == standard.kind):
            continue
        if p.composition_verified and len(set(p.app_ids)) < 2 and not EDITION.search(p.name):
            continue
        reason = None
        if base.app_type != "game":
            reason = "기준 App이 본편 게임이 아님"
        elif not p.composition_verified or base.id not in p.app_ids:
            reason = "본편 포함 구성 미확인"
        elif len(set(p.app_ids) - {base.id}) == 0:
            reason = "추가 콘텐츠 미확인"
        elif not p.unconditional:
            reason = "별도 구매 조건 또는 개인화 번들 여부 확인 필요"
        elif p.currency != "KRW" or p.country != "KR":
            reason = "대한민국 KRW 가격 아님"
        elif p.price is None or p.price <= 0:
            reason = "유효한 유료 가격 없음"
        elif not standard or standard.price <= 0:
            reason = "본편만 포함된 일반판 패키지의 유효 가격 없음"
        elif not p.scan_id or p.scan_id != standard.scan_id:
            reason = "서로 다른 수집 실행"
        elif abs((datetime.fromisoformat(p.collected_at) - datetime.fromisoformat(standard.collected_at)).total_seconds()) > max_age_seconds:
            reason = "가격 수집 시각 차이 초과"
        entry = {"base_app_id": base.id, "base_name": base.name,
                 "standard": standard.to_dict() if standard else None, "edition": p.to_dict()}
        if reason:
            unverified.append({**entry, "status": "확인 필요", "reason": reason})
        elif p.price < standard.price:
            confirmed.append({**entry, "status": "구성 검증 완료",
                              "difference": standard.price - p.price,
                              "inversion_percent": round((standard.price - p.price) / standard.price * 100, 2)})
    return confirmed, unverified
