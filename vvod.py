"""Ввод с клавиатуры: числа, да/нет и позиции целиком."""

from decimal import Decimal, InvalidOperation

import stavki


def chislo(vopros, po_umolchaniyu=None, min_znach=Decimal("0")):
    """Спрашивает, пока не введут нормальное число. Понимает и 12,5 и 12.5"""
    podskazka = f" [{po_umolchaniyu}]" if po_umolchaniyu is not None else ""
    while True:
        otvet = input(f"{vopros}{podskazka}: ").strip().replace(" ", "").replace(",", ".")
        if otvet == "" and po_umolchaniyu is not None:
            return Decimal(str(po_umolchaniyu))
        try:
            znach = Decimal(otvet)
        except InvalidOperation:
            print("  Нужно число, например 1500 или 12,5. Попробуйте ещё раз.")
            continue
        if znach < min_znach:
            print(f"  Число не может быть меньше {min_znach}.")
            continue
        return znach


def tekst(vopros, po_umolchaniyu=None):
    podskazka = f" [{po_umolchaniyu}]" if po_umolchaniyu else ""
    while True:
        otvet = input(f"{vopros}{podskazka}: ").strip()
        if otvet:
            return otvet
        if po_umolchaniyu:
            return po_umolchaniyu
        print("  Поле не может быть пустым.")


def da_net(vopros, po_umolchaniyu="д"):
    while True:
        otvet = input(f"{vopros} (д/н) [{po_umolchaniyu}]: ").strip().lower() or po_umolchaniyu
        if otvet in ("д", "да", "y", "yes"):
            return True
        if otvet in ("н", "нет", "n", "no"):
            return False
        print("  Ответьте «д» или «н».")


def vvesti_tovar(nomer, valyuta):
    print(f"\n--- Позиция №{nomer} ---")
    t = {}
    vid = tekst("Товар или услуга нерезидента? (т/у)", "т").lower()
    if vid.startswith("у"):
        t["vid"] = "usluga"
        t["naimenovanie"] = tekst("Наименование услуги")
        t["kolichestvo"] = chislo("Количество", 1, min_znach=Decimal("0.001"))
        t["tsena"] = chislo(f"Стоимость по договору за единицу, {valyuta}")
        t["strana"] = tekst("Страна нерезидента")
        t["ndn_stavka"] = chislo("Ставка НДН, %", stavki.NDN_STAVKA)
        t["ndn_sverhu"] = da_net("НДН платим за свой счёт сверху суммы договора "
                                 "(нерезидент получает полную сумму)?", "д")
        t["poshlina_stavka"] = t["akciz_stavka"] = Decimal("0")
        return t

    t["vid"] = "tovar"
    t["naimenovanie"] = tekst("Наименование")
    t["kolichestvo"] = chislo("Количество", min_znach=Decimal("0.001"))
    t["tsena"] = chislo(f"Цена за единицу, {valyuta}")
    t["strana"] = tekst("Страна происхождения")

    if t["strana"].strip().lower() in stavki.STRANY_EAES:
        print("  Страна ЕАЭС — ввозная пошлина 0%.")
        t["poshlina_stavka"] = Decimal("0")
    else:
        print("  Страна вне ЕАЭС — нужна ставка пошлины по коду ТН ВЭД (ЕТТ ЕАЭС).")
        t["poshlina_stavka"] = chislo("Ставка ввозной пошлины, %", 0)

    t["akciz_stavka"] = chislo("Ставка акциза, % (если не подакцизный — 0)", 0)
    return t
