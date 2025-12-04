def dedupe_by_key(existing, new_list, key="id"):
    seen = {item.get(key) for item in existing if item.get(key)}
    merged = []
    added = 0
    deduped = 0

    for item in new_list:
        k = item.get(key)
        if k and k not in seen:
            merged.append(item)
            seen.add(k)
            added += 1
        else:
            deduped += 1

    merged = existing + merged
    return merged, added, deduped
