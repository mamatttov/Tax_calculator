"""Сам расчёт: себестоимость, налоги, цена продажи, прибыль."""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

import stavki

TIYIN = Decimal("0.01")


def okrugl(x):
    """До тыйына."""
    return x.quantize(TIYIN, rounding=ROUND_HALF_UP)


def raschet(tovary, kurs, dostavka, sbor_stavka, prochie, platelshik_nds, natsenka,
            nalog_vyruchka=Decimal("0"), vverh=True):
    # доставку и прочие расходы раскидываем только на товары, по их стоимости
    stoimost_vsego = sum(t["tsena"] * t["kolichestvo"] for t in tovary
                         if t.get("vid", "tovar") == "tovar")

    for t in tovary:
        stoimost_val = t["tsena"] * t["kolichestvo"]
        if t.get("vid") == "usluga":
            raschet_uslugi(t, stoimost_val, kurs, platelshik_nds)
            prodazha(t, platelshik_nds, natsenka, nalog_vyruchka, vverh)
            continue
        t["ndn"] = Decimal("0")
        dolya = stoimost_val / stoimost_vsego if stoimost_vsego else Decimal("0")

        # тамож. стоимость = цена + доставка до границы
        t["stoimost_som"] = okrugl(stoimost_val * kurs)
        t["dostavka_som"] = okrugl(dostavka * kurs * dolya)
        t["tam_stoimost"] = t["stoimost_som"] + t["dostavka_som"]
        t["stoimost"] = t["tam_stoimost"]

        t["poshlina"] = okrugl(t["tam_stoimost"] * t["poshlina_stavka"] / 100)
        t["akciz"] = okrugl((t["tam_stoimost"] + t["poshlina"]) * t["akciz_stavka"] / 100)

        t["sbor"] = okrugl(t["tam_stoimost"] * sbor_stavka / 100)

        # сбор входит в базу НДС, так же считаем и в excel
        t["baza_nds"] = t["tam_stoimost"] + t["poshlina"] + t["akciz"] + t["sbor"]
        t["nds"] = okrugl(t["baza_nds"] * stavki.NDS_STAVKA / 100)

        t["prochie"] = okrugl(prochie * dolya)

        # плательщик НДС берёт его в зачёт, остальным он идёт в себестоимость
        t["sebestoimost"] = (t["tam_stoimost"] + t["poshlina"] + t["akciz"]
                             + t["sbor"] + t["prochie"]
                             + (Decimal("0") if platelshik_nds else t["nds"]))
        t["sebest_ed"] = okrugl(t["sebestoimost"] / t["kolichestvo"])
        prodazha(t, platelshik_nds, natsenka, nalog_vyruchka, vverh)
        t["k_oplate"] = t["poshlina"] + t["akciz"] + t["nds"] + t["sbor"]
    return tovary


def raschet_uslugi(t, stoimost_val, kurs, platelshik_nds):
    """Услуга нерезидента: таможни нет, зато НДН и НДС за нерезидента.

    Если НДН платим сверху, база = сумма / (1 - НДН), иначе база = сумма.
    НДН и НДС считаются от этой базы.
    """
    summa = okrugl(stoimost_val * kurs)
    stavka = t["ndn_stavka"] / 100
    t["tam_stoimost"] = okrugl(summa / (1 - stavka)) if t["ndn_sverhu"] else summa
    t["ndn"] = okrugl(t["tam_stoimost"] * stavka)
    t["nds"] = okrugl(t["tam_stoimost"] * stavki.NDS_STAVKA / 100)
    t["poshlina"] = t["akciz"] = t["sbor"] = t["prochie"] = Decimal("0")
    # себестоимость = цена поставщика + НДН + НДС
    t["stoimost"] = summa
    t["sebestoimost"] = (summa + (t["ndn"] if t["ndn_sverhu"] else Decimal("0"))
                         + (Decimal("0") if platelshik_nds else t["nds"]))
    t["sebest_ed"] = okrugl(t["sebestoimost"] / t["kolichestvo"])
    t["k_oplate"] = t["ndn"] + t["nds"]


def prodazha(t, platelshik_nds, natsenka, nalog_vyruchka, vverh=True):
    # единый налог закладываем в цену, чтобы наценка осталась чистой
    tsena_bez_nds = t["sebest_ed"] * (1 + natsenka / 100) / (1 - nalog_vyruchka / 100)
    # как ОКРУГЛВВЕРХ(...; 0) в экселе
    tsena_bez_nds = tsena_bez_nds.quantize(Decimal("1"), rounding=ROUND_CEILING) \
        if vverh else tsena_bez_nds
    t["tsena_bez_nds_ed"] = okrugl(tsena_bez_nds)
    t["tsena_prodazhi_ed"] = okrugl(tsena_bez_nds * (1 + stavki.NDS_STAVKA / 100)) \
        if platelshik_nds else t["tsena_bez_nds_ed"]
    t["vyruchka"] = okrugl(t["tsena_bez_nds_ed"] * t["kolichestvo"])
    t["nalog_vyruchka"] = okrugl(t["vyruchka"] * nalog_vyruchka / 100)
    t["pribyl"] = t["vyruchka"] - t["nalog_vyruchka"] - t["sebestoimost"]
