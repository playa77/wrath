# Version: 0.2.0 | 2026-11-02
"""Registry-driven kit, stock, tonics, trade and distribution (BR-8–10)."""

import math
from .support import member as get_member, party, require, item_instance, held, emit
from . import events, body, quests


def usable(e, m, item):
    row = e.items[item["item_id"] if isinstance(item, dict) else item]
    req = row.get("prereq", {})
    if (
        isinstance(item, dict)
        and item.get("elder")
        and "elder" not in row.get("flags", [])
    ):
        req = {k: math.ceil(v * 2 / 3) for k, v in req.items()}
    attrs = m["attrs"]
    return all(
        (
            2 * attrs["str"] + attrs["dex"]
            if key == "twostr_plus_dex"
            else attrs.get(key, 0)
        )
        >= value
        for key, value in req.items()
    )


def open_stock(e, post=None, vendor=False):
    p = e.lookup("posts", post or e.s["post_context"])
    band = (
        1 + max(abs(p["pos"][0] // 15 - 2), abs(p["pos"][1] // 10 - 2))
        if p["map_id"] == "province"
        else 3
    )
    choices = [
        i
        for i in e.items.values()
        if i["family"] in ["weapon", "armor", "shield", "fire", "tonic"]
        and (i["value"] >= 8 if vendor else i["value"] <= max(3, band * 5))
    ]
    # Every available rung is listed, ordered by family and value; per-visit RNG
    # selects a rotating front page without removing essential stock.
    if choices:
        offset = e.rng.pick(list(range(len(choices))))
        choices = choices[offset:] + choices[:offset]
    folios = [
        r
        for r in e.data["folio_items"]
        if ("Terminus" in r.get("location", "") and p["id"] == 1)
        or p["name"] in r.get("location", "")
        or r.get("sealed")
        or r["id"].startswith("club_gazette")
    ]
    e.s["stock"] = [r["id"] for r in choices + folios]
    e.s["shop_page"] = 0


def list_page(e, page=0, member=None, **a):
    if not e.s["stock"]:
        open_stock(e)
    if a.get("next"):
        page = e.s.get("shop_page", 0) + 1
    page = int(page)
    require(page >= 0, "runtime_invalid_page")
    e.s["shop_page"] = page
    shopper = get_member(e, member)
    rows = []
    for index, ident in enumerate(
        e.s["stock"][page * 12 : (page + 1) * 12], page * 12 + 1
    ):
        row = e.items[ident]
        rows.append(
            dict(
                no=index,
                item_id=ident,
                family=row["family"],
                name=row["name"],
                cost=row["cost"],
                value=row["value"],
                unusable=not usable(e, shopper, ident),
            )
        )
    return [
        events.state({"stock": rows}),
        events.menu("outfitter", {"page": page}, rows),
    ]


def buy(e, member=None, item_no=None, item_id=None, skin="bow", **a):
    if not e.s["stock"]:
        open_stock(e)
    if item_id is None:
        require(
            type(item_no) == int and 1 <= item_no <= len(e.s["stock"]),
            "runtime_invalid_stock_number",
        )
        item_id = e.s["stock"][item_no - 1]
    require(item_id in e.s["stock"], "runtime_item_is_not_stocked")
    require(skin in ["bow", "rifle"], "runtime_invalid_fire_skin")
    m = get_member(e, member, living=True)
    row = e.items[item_id]
    require(len(m["items"]) < e.rules["kit_cap"], e.text("full"))
    price = int(row["cost"] * e.lookup("strains", m["strain"])["fee_multiplier"])
    require(e.s["expedition"]["treasury"] >= price, e.text("afford"))
    e.s["expedition"]["treasury"] -= price
    inst = item_instance(e, item_id, skin)
    m["items"].append(inst)
    if usable(e, m, inst) and row["family"] in ["weapon", "armor", "shield", "fire"]:
        m["in_use"][row["family"]] = item_id
    return [events.state({"bought": item_id})]


def kit_item(m, item):
    if type(item) == int:
        require(1 <= item <= len(m["items"]), "runtime_invalid_kit_number")
        return m["items"][item - 1]
    inst = next((i for i in m["items"] if i["item_id"] == item), None)
    require(inst is not None, "runtime_item_is_not_carried")
    return inst


def sell(e, item, member=None, **a):
    m = get_member(e, member)
    inst = kit_item(m, item)
    require(not inst["bound"], e.text("bound"))
    row = e.items[inst["item_id"]]
    value = int(row["cost"] * e.rules["sell_fraction"])
    require(
        e.s["expedition"]["treasury"] + value <= e.rules["treasury_cap"],
        e.text("overflow"),
    )
    e.s["expedition"]["treasury"] += value
    m["items"].remove(inst)
    for key, ident in list(m["in_use"].items()):
        if ident == inst["item_id"] and not any(
            i["item_id"] == ident for i in m["items"]
        ):
            del m["in_use"][key]
    return [events.state({"sold": inst["item_id"]})]


def use_item(e, item, member=None, target_member=None, **a):
    m = get_member(e, member, living=True)
    inst = kit_item(m, item)
    row = e.items[inst["item_id"]]
    if (
        row["id"] in ["sweet_phial", "foul_phial"]
        and e.s["world"]["map_id"] == "site04"
    ):
        e.s["world"]["sites"]["site04"]["flags"]["scent"] = row["id"]
        return emit(
            "DLG-045"
            if row["id"] == "sweet_phial"
            else "The foul scent drives the viper back."
        )
    if row["family"] == "folio":
        require(e.s["phase"] == "post", "runtime_read_folios_at_a_post")
        if row.get("sealed"):
            return emit("sealed")
        text = (
            e.lookup("folios", row["payload"])["text"]
            if row.get("payload")
            else row["text"]
        )
        return emit(text)
    if row["family"] == "tonic":
        target = get_member(e, target_member or m["id"], living=True)
        require(
            target["id"] in e.s["expedition"]["members"],
            "runtime_target_is_not_in_expedition",
        )
        if "hp" in row:
            body.heal(e, target, row["hp"], row["cure_tier"])
        if "mp" in row:
            target["mp_cur"] = min(target["mp_max"], target["mp_cur"] + row["mp"])
        m["items"].remove(inst)
        return [events.state({"used": row["id"], "target": target["id"]})]
    if row["family"] in ["weapon", "armor", "shield", "fire"]:
        require(usable(e, m, inst), e.text("unusable"))
        m["in_use"][row["family"]] = row["id"]
        return [events.state({"equipped": row["name"]})]
    return emit(row["name"])


def distribute(e, item=None, member=None, **a):
    pool = e.s["expedition"]["found_items"]
    if item is None:
        ordered = sorted(
            pool,
            key=lambda i: (
                "elder" in e.items[i["item_id"]].get("flags", []),
                e.items[i["item_id"]]["value"],
            ),
            reverse=True,
        )
        return [
            events.state(
                {
                    "pool": [
                        dict(
                            **i, usability={m["id"]: usable(e, m, i) for m in party(e)}
                        )
                        for i in ordered
                    ]
                }
            ),
            events.menu(
                "distribute",
                {},
                [
                    dict(
                        key=str(index + 1),
                        label=e.items[i["item_id"]]["name"],
                        verb="post.distribute",
                        args={"item": index + 1},
                    )
                    for index, i in enumerate(pool)
                ],
            ),
        ]
    require(type(item) == int and 1 <= item <= len(pool), "runtime_invalid_pool_number")
    m = get_member(e, member)
    require(len(m["items"]) < e.rules["kit_cap"], e.text("full"))
    inst = pool.pop(item - 1)
    m["items"].append(inst)
    row = e.items[inst["item_id"]]
    if row["family"] in ["weapon", "shield", "armor", "fire"] and usable(e, m, inst):
        m["in_use"][row["family"]] = row["id"]
    return [events.state({"distributed": inst["item_id"]})]


def trade(e, src_member, dst_member, item, **a):
    if a.get("sell") or (dst_member == 7 and 7 not in e.s["expedition"]["members"]):
        return sell(e, item, member=src_member)
    src = get_member(e, src_member)
    dst = get_member(e, dst_member)
    inst = kit_item(src, item)
    require(not inst["bound"], e.text("bound"))
    require(len(dst["items"]) < e.rules["kit_cap"], e.text("full"))
    src["items"].remove(inst)
    dst["items"].append(inst)
    for key, ident in list(src["in_use"].items()):
        if ident == inst["item_id"]:
            del src["in_use"][key]
    return [events.state({"traded": inst["item_id"]})]


def give(e, ident, unique=False):
    row = e.items[ident]
    if row.get("unique") and (e.s["flags"].get("collected." + ident) or held(e, ident)):
        return []
    inst = item_instance(e, ident, "bow")
    if inst["bound"]:
        m = next((m for m in party(e) if len(m["items"]) < e.rules["kit_cap"]), None)
        if m:
            m["items"].append(inst)
        else:
            require(
                len(e.s["expedition"]["found_items"]) < e.rules["found_cap"],
                "runtime_found_items_pool_full",
            )
            e.s["expedition"]["found_items"].append(inst)
    else:
        require(
            len(e.s["expedition"]["found_items"]) < e.rules["found_cap"],
            "runtime_found_items_pool_full",
        )
        e.s["expedition"]["found_items"].append(inst)
    if row.get("unique"):
        e.s["flags"]["collected." + ident] = True
    if ident in ["sun_key", "drowned_key", "sun_gem"]:
        e.s["flags"][ident] = True
    if ident == "crystal_resonator":
        e.s["flags"]["resonator_held"] = True
    quests.update_score(e)
    return [events.state({"found": ident})]
