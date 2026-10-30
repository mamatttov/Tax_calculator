"""Калькулятор себестоимости импорта, версия для терминала.

    .\\.venv\\Scripts\\python.exe main.py

Окно: okno.py
"""

from datetime import datetime
from decimal import Decimal

import stavki
from otchet import pechat, sohranit_excel
from raschet import raschet
from vvod import chislo, da_net, tekst, vvesti_tovar


def main():
    print("Калькулятор себестоимости импорта")
    print("в [скобках] значение по умолчанию, можно просто нажать Enter\n")

    valyuta = tekst("Валюта инвойса (USD, CNY, RUB, KZT...)", "USD").upper()
    if valyuta in ("KGS", "СОМ"):
        kurs = Decimal("1")
    elif da_net(f"Считать всё в {valyuta} (без перевода в сомы)?", "н"):
        kurs = Decimal("1")
        stavki.VAL_NAZV = valyuta
    else:
        kurs = chislo(f"Курс НБКР: сколько сом за 1 {valyuta}", min_znach=Decimal("0.0001"))

    tovary = []
    while True:
        tovary.append(vvesti_tovar(len(tovary) + 1, valyuta))
        if not da_net("Добавить ещё товар?", "н"):
            break

    print("\n--- Общие расходы на всю партию (делятся пропорционально стоимости) ---")
    dostavka = chislo(f"Доставка до границы КР, {valyuta}", 0)
    sbor = chislo("Таможенный сбор, % от таможенной стоимости", stavki.SBOR_STAVKA)
    prochie = chislo(f"Брокер, склад, доставка по КР и прочее, {stavki.VAL_NAZV}", 0)
    platelshik_nds = da_net("Ваша организация — плательщик НДС (НДС к зачёту)?", "н")
    natsenka = chislo("Наценка, %", 0)
    nalog = chislo("Налог с выручки (единый налог / налог с продаж), %", 0)
    while nalog >= 100:
        print("  Ставка должна быть меньше 100.")
        nalog = chislo("Налог с выручки, %", 0)

    vverh = da_net("Округлять цену продажи вверх до целого?", "д")

    raschet(tovary, kurs, dostavka, sbor, prochie, platelshik_nds, natsenka, nalog, vverh)
    pechat(tovary, platelshik_nds)

    shapka = [
        ["Расчёт себестоимости импорта", datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Валюта", valyuta, "Курс", float(kurs), "Суммы в", stavki.VAL_NAZV],
        ["Тамож. сбор, %", float(sbor)],
        ["НДС, %", float(stavki.NDS_STAVKA), "Плательщик НДС", "да" if platelshik_nds else "нет"],
        ["Наценка, %", float(natsenka), "Налог с выручки, %", float(nalog)],
    ]
    imya = f"raschet_{datetime.now():%Y-%m-%d_%H-%M}.xlsx"
    sohranit_excel(tovary, shapka, imya)
    print("\n(ставки пошлины, акциза и НДС лучше перепроверить)")


if __name__ == "__main__":
    main()
