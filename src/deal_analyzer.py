def find_deals(products, min_discount=90, max_price=5000):
    unique = {(p.kind, p.id): p for p in products}
    return sorted((p for p in unique.values()
                   if p.kind == "app" and p.app_type == "game"
                   and p.country == "KR" and p.currency == "KRW"
                   and p.price is not None and 0 < p.price <= max_price
                   and p.discount >= min_discount), key=lambda p: (-p.discount, p.price, p.id))
