"""Окошко для калькулятора. Расчёт в raschet.py, ставки в stavki.py.

    .\\.venv\\Scripts\\python.exe okno.py

Собрать exe: build_exe.bat
"""

import tkinter as tk
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import ttk, messagebox, filedialog

import stavki
from otchet import sohranit_excel
from raschet import raschet

# цвета
FON = "#f4f6f9"
KARTOCHKA = "#ffffff"
AKCENT = "#2563eb"
TEKST = "#1f2937"
SERYY = "#6b7280"
SHRIFT = ("Segoe UI", 10)

STRANY = ["Китай", "Турция", "Россия", "Казахстан", "Беларусь", "Армения",
          "Узбекистан", "Корея", "Германия", "США", "ОАЭ", "Индия"]
VALYUTY = ["USD", "CNY", "RUB", "KZT", "EUR", "KGS"]


def v_chislo(stroka, nazvanie, mozhno_pusto=True):
    """Текст из поля -> Decimal, пустое поле считаем нулём."""
    s = stroka.strip().replace(" ", "").replace(",", ".")
    if s == "" and mozhno_pusto:
        return Decimal("0")
    try:
        x = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Поле «{nazvanie}»: нужно число, например 1500 или 12,5")
    if x < 0:
        raise ValueError(f"Поле «{nazvanie}»: число не может быть отрицательным")
    return x


def som(x):
    """12345.6 -> '12 345,60'"""
    return f"{x:,.2f}".replace(",", " ").replace(".", ",")


class Prilozhenie(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор себестоимости импорта")
        self.geometry("1320x860")
        self.minsize(1000, 600)
        self.configure(bg=FON)
        self.tovary = []
        self.nastroit_stil()
        self.sozdat_parametry()
        self.sozdat_formu_tovara()
        self.sozdat_tablitsu()
        self.sozdat_itogi()
        self.pereschitat()

    # --- оформление ---
    def nastroit_stil(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", font=SHRIFT, background=FON, foreground=TEKST)
        s.configure("Card.TLabelframe", background=KARTOCHKA, bordercolor="#d1d5db")
        s.configure("Card.TLabelframe.Label", background=KARTOCHKA,
                    foreground=AKCENT, font=("Segoe UI", 11, "bold"))
        s.configure("Card.TLabel", background=KARTOCHKA)
        s.configure("Hint.TLabel", background=KARTOCHKA, foreground=SERYY,
                    font=("Segoe UI", 9))
        s.configure("Card.TCheckbutton", background=KARTOCHKA)
        s.configure("Card.TRadiobutton", background=KARTOCHKA,
                    font=("Segoe UI", 10, "bold"))
        s.configure("Accent.TButton", background=AKCENT, foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=(14, 6))
        s.map("Accent.TButton", background=[("active", "#1d4ed8")])
        s.configure("TButton", padding=(10, 5))
        s.configure("Treeview", rowheight=26, font=SHRIFT)
        s.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"),
                    background="#e5e7eb")
        s.configure("Total.TLabel", background=KARTOCHKA, font=("Segoe UI", 11))
        s.configure("Profit.TLabel", background=KARTOCHKA, foreground="#15803d",
                    font=("Segoe UI", 13, "bold"))
        s.configure("TotalBig.TLabel", background=KARTOCHKA, foreground=AKCENT,
                    font=("Segoe UI", 13, "bold"))

    def pole(self, roditel, podpis, stroka, kolonka, shirina=12, znach=""):
        ttk.Label(roditel, text=podpis, style="Card.TLabel").grid(
            row=stroka, column=kolonka, sticky="w", padx=(10, 4), pady=4)
        var = tk.StringVar(value=znach)
        e = ttk.Entry(roditel, textvariable=var, width=shirina)
        e.grid(row=stroka, column=kolonka + 1, sticky="w", padx=(0, 10), pady=4)
        return var, e

    # --- параметры партии ---
    def sozdat_parametry(self):
        f = ttk.LabelFrame(self, text=" Параметры партии ", style="Card.TLabelframe",
                           padding=8)
        f.pack(fill="x", padx=14, pady=(14, 6))

        ttk.Label(f, text="Валюта", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", padx=(10, 4))
        self.valyuta = tk.StringVar(value="USD")
        cb = ttk.Combobox(f, textvariable=self.valyuta, values=VALYUTY, width=8)
        cb.grid(row=0, column=1, sticky="w", padx=(0, 10))
        cb.bind("<<ComboboxSelected>>", lambda e: self.pereschitat())

        self.kurs, self.e_kurs = self.pole(f, "Курс НБКР (сом за 1)", 0, 2, 10)
        self.dostavka, _ = self.pole(f, "Доставка до границы (валюта)", 0, 4, 10)
        self.nds, _ = self.pole(f, "НДС, %", 0, 6, 6, str(stavki.NDS_STAVKA))
        f.columnconfigure(8, weight=1)

        self.sbor, _ = self.pole(f, "Тамож. сбор, % от стоим.", 1, 0, 10, str(stavki.SBOR_STAVKA))
        self.prochie, _ = self.pole(f, "Брокер, склад, прочее", 1, 2, 10)
        self.natsenka, _ = self.pole(f, "Наценка, %", 1, 4, 10, "0")
        self.nalog, _ = self.pole(f, "Налог с выручки, %", 2, 0, 10, "0")
        ttk.Label(f, text="единый налог или налог с продаж — по вашему режиму",
                  style="Hint.TLabel").grid(row=2, column=2, columnspan=3, sticky="w",
                                            padx=10)
        self.platelshik = tk.BooleanVar(value=False)
        self.v_valyute = tk.BooleanVar(value=False)
        self.vverh = tk.BooleanVar(value=True)
        for i, (var, nazv, komanda) in enumerate([
                (self.platelshik, "Плательщик НДС (НДС к зачёту)", self.pereschitat),
                (self.v_valyute, "Считать в валюте (без курса)", self.smena_valyuty),
                (self.vverh, "Округлять цену вверх до целого", self.pereschitat)]):
            ttk.Checkbutton(f, text=nazv, variable=var, style="Card.TCheckbutton",
                            command=komanda).grid(row=i + 1, column=6, columnspan=2,
                                                  sticky="w", padx=(10, 4))

        ttk.Label(f, text="Ставки НДС, пошлины и акциза сверяйте с действующим НК КР "
                          "и ЕТТ ЕАЭС.", style="Hint.TLabel").grid(
            row=3, column=0, columnspan=8, sticky="w", padx=10, pady=(4, 0))

        for var in (self.kurs, self.dostavka, self.nds, self.sbor, self.prochie,
                    self.natsenka, self.nalog):
            var.trace_add("write", lambda *a: self.pereschitat())

    def smena_valyuty(self):
        self.e_kurs.state(["disabled"] if self.v_valyute.get() else ["!disabled"])
        self.pereschitat()

    # --- ввод товара ---
    def sozdat_formu_tovara(self):
        f = ttk.LabelFrame(self, text=" Добавить позицию ", style="Card.TLabelframe",
                           padding=8)
        f.pack(fill="x", padx=14, pady=6)

        self.vid = tk.StringVar(value="tovar")
        for i, (znach, nazv) in enumerate([("tovar", "Товар (импорт)"),
                                           ("usluga", "Услуга нерезидента")]):
            ttk.Radiobutton(f, text=nazv, value=znach, variable=self.vid,
                            style="Card.TRadiobutton", command=self.smena_vida).grid(
                row=0, column=i * 2, columnspan=2, sticky="w", padx=10, pady=(0, 4))

        self.naim, e_naim = self.pole(f, "Наименование", 1, 0, 28)
        self.kol, _ = self.pole(f, "Количество", 1, 2, 8)
        self.tsena, _ = self.pole(f, "Цена за ед.", 1, 4, 10)

        ttk.Label(f, text="Страна", style="Card.TLabel").grid(
            row=1, column=6, sticky="w", padx=(10, 4))
        self.strana = tk.StringVar()
        cb = ttk.Combobox(f, textvariable=self.strana, values=STRANY, width=14)
        cb.grid(row=1, column=7, sticky="w", padx=(0, 10))
        self.strana.trace_add("write", lambda *a: self.proverit_eaes())

        # для товара
        self.poshlina, self.e_poshlina = self.pole(f, "Пошлина, %", 2, 0, 8, "0")
        self.akciz, _ = self.pole(f, "Акциз, %", 2, 2, 8, "0")
        self.polya_tovara = f.grid_slaves(row=2)
        # для услуги, по умолчанию спрятаны
        self.ndn, _ = self.pole(f, "НДН, %", 2, 0, 8, str(stavki.NDN_STAVKA))
        self.ndn_sverhu = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="НДН сверху (за свой счёт)",
                        variable=self.ndn_sverhu, style="Card.TCheckbutton").grid(
            row=2, column=2, columnspan=3, sticky="w", padx=10)
        self.polya_uslugi = [w for w in f.grid_slaves(row=2)
                             if w not in self.polya_tovara]
        for w in self.polya_uslugi:
            w.grid_remove()

        self.podskazka_eaes = ttk.Label(f, text="", style="Hint.TLabel")
        self.podskazka_eaes.grid(row=3, column=0, columnspan=6, sticky="w", padx=10)

        knopki = ttk.Frame(f, style="Card.TLabel")
        knopki.grid(row=2, column=6, columnspan=2, sticky="e", padx=10)
        ttk.Button(knopki, text="+ Добавить", style="Accent.TButton",
                   command=self.dobavit).pack(side="left")

        self.e_naim = e_naim
        self.bind("<Return>", lambda e: self.dobavit())
        e_naim.focus_set()

    def smena_vida(self):
        usluga = self.vid.get() == "usluga"
        for w in self.polya_tovara:
            w.grid_remove() if usluga else w.grid()
        for w in self.polya_uslugi:
            w.grid() if usluga else w.grid_remove()
        self.proverit_eaes()

    def proverit_eaes(self):
        if self.vid.get() == "usluga":
            self.podskazka_eaes.config(text="НДН и НДС за нерезидента — проверьте ставки")
            return
        if self.strana.get().strip().lower() in stavki.STRANY_EAES:
            self.poshlina.set("0")
            self.e_poshlina.state(["disabled"])
            self.podskazka_eaes.config(text="Страна ЕАЭС: пошлина 0%")
        else:
            self.e_poshlina.state(["!disabled"])
            self.podskazka_eaes.config(text="Вне ЕАЭС: ставка по коду ТН ВЭД")

    def dobavit(self):
        try:
            naim = self.naim.get().strip()
            strana = self.strana.get().strip()
            if not naim:
                raise ValueError("Заполните наименование")
            if not strana:
                raise ValueError("Укажите страну")
            kol = v_chislo(self.kol.get(), "Количество", mozhno_pusto=False)
            if kol == 0:
                raise ValueError("Количество должно быть больше нуля")
            t = {
                "naimenovanie": naim,
                "kolichestvo": kol,
                "tsena": v_chislo(self.tsena.get(), "Цена", mozhno_pusto=False),
                "strana": strana,
                "poshlina_stavka": v_chislo(self.poshlina.get(), "Пошлина"),
                "akciz_stavka": v_chislo(self.akciz.get(), "Акциз"),
                "vid": self.vid.get(),
            }
            if t["vid"] == "usluga":
                t["poshlina_stavka"] = t["akciz_stavka"] = Decimal("0")
                t["ndn_stavka"] = v_chislo(self.ndn.get(), "НДН")
                if t["ndn_stavka"] >= 100:
                    raise ValueError("Ставка НДН должна быть меньше 100")
                t["ndn_sverhu"] = self.ndn_sverhu.get()
        except ValueError as oshibka:
            messagebox.showwarning("Проверьте данные", str(oshibka))
            return
        self.tovary.append(t)
        for var in (self.naim, self.kol, self.tsena):
            var.set("")
        self.akciz.set("0")
        self.e_naim.focus_set()
        self.pereschitat()

    # --- таблица ---
    def sozdat_tablitsu(self):
        f = ttk.LabelFrame(self, text=" Расчёт по позициям ", style="Card.TLabelframe",
                           padding=8)
        f.pack(fill="both", expand=True, padx=14, pady=6)

        self.kolonki = [
            ("naimenovanie", "Наименование", 130, "w"),
            ("strana", "Страна", 80, "w"),
            ("kolichestvo", "Кол-во", 55, "e"),
            ("tsena", "Цена (вал.)", 75, "e"),
            ("stoimost", "Стоимость", 100, "e"),
            ("poshl_akciz", "Пошл.+акц.", 85, "e"),
            ("ndn", "НДН", 70, "e"),
            ("nds", "НДС", 85, "e"),
            ("rashody", "Сборы+проч.", 90, "e"),
            ("sebestoimost", "Себестоимость", 105, "e"),
            ("sebest_ed", "Себест. ед.", 85, "e"),
            ("tsena_prodazhi_ed", "Продажа ед.", 90, "e"),
            ("nalog_vyruchka", "Налог", 80, "e"),
            ("pribyl", "Прибыль", 95, "e"),
        ]
        self.tablitsa = ttk.Treeview(f, columns=[c[0] for c in self.kolonki],
                                     show="headings", selectmode="extended",
                                     height=8)
        for kl, nazv, shir, rovn in self.kolonki:
            self.tablitsa.heading(kl, text=nazv)
            self.tablitsa.column(kl, width=shir, anchor=rovn, stretch=kl == "naimenovanie")
        self.tablitsa.tag_configure("chet", background="#f9fafb")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tablitsa.yview)
        self.tablitsa.configure(yscrollcommand=sb.set)
        self.tablitsa.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tablitsa.bind("<Delete>", lambda e: self.udalit())

    # --- итоги и кнопки ---
    def sozdat_itogi(self):
        f = ttk.Frame(self, style="Card.TLabel", padding=10)
        f.pack(fill="x", padx=14, pady=(6, 14))

        self.itogi = {}
        spisok = [("stoimost", "Стоимость (цена)", "Total.TLabel"),
                  ("k_oplate", "В бюджет (пошл., НДС, НДН)", "Total.TLabel"),
                  ("vyruchka", "Выручка без НДС", "Total.TLabel"),
                  ("nalog_vyruchka", "Налог с выручки", "Total.TLabel"),
                  ("sebestoimost", "Себестоимость партии", "TotalBig.TLabel"),
                  ("pribyl", "ПРИБЫЛЬ", "Profit.TLabel")]
        for i, (kl, nazv, stil) in enumerate(spisok):
            ttk.Label(f, text=nazv, style="Hint.TLabel").grid(row=0, column=i, sticky="w",
                                                              padx=12)
            lbl = ttk.Label(f, text="0,00", style=stil)
            lbl.grid(row=1, column=i, sticky="w", padx=12)
            self.itogi[kl] = lbl
        self.podpis_itogov = ttk.Label(f, text="", style="Hint.TLabel")
        self.podpis_itogov.grid(row=2, column=0, sticky="w", padx=12)
        self.marzha = ttk.Label(f, text="", style="Hint.TLabel")
        self.marzha.grid(row=2, column=5, sticky="w", padx=12)

        knopki = ttk.Frame(f, style="Card.TLabel")
        knopki.grid(row=3, column=0, columnspan=7, sticky="e", padx=8, pady=(10, 0))
        f.columnconfigure(6, weight=1)
        ttk.Button(knopki, text="Удалить выбранное", command=self.udalit).pack(
            side="left", padx=4)
        ttk.Button(knopki, text="Очистить всё", command=self.ochistit).pack(
            side="left", padx=4)
        ttk.Button(knopki, text="Сохранить в Excel", style="Accent.TButton",
                   command=self.excel).pack(side="left", padx=4)

    # --- логика ---
    def parametry(self):
        """Параметры партии из полей. Кривое число -> ValueError."""
        valyuta = self.valyuta.get().strip().upper() or "USD"
        if valyuta in ("KGS", "СОМ") or self.v_valyute.get():
            kurs = Decimal("1")
        else:
            kurs = v_chislo(self.kurs.get(), "Курс")
        p = {
            "valyuta": valyuta,
            "kurs": kurs,
            "dostavka": v_chislo(self.dostavka.get(), "Доставка"),
            "sbor": v_chislo(self.sbor.get(), "Таможенный сбор"),
            "prochie": v_chislo(self.prochie.get(), "Прочие"),
            "natsenka": v_chislo(self.natsenka.get(), "Наценка"),
            "nalog": v_chislo(self.nalog.get(), "Налог с выручки"),
            "nds": v_chislo(self.nds.get(), "НДС"),
            "platelshik": self.platelshik.get(),
            "vverh": self.vverh.get(),
            "val_nazv": valyuta if self.v_valyute.get() else "сом",
        }
        if p["nalog"] >= 100:
            raise ValueError("Поле «Налог с выручки»: ставка должна быть меньше 100")
        return p

    def pereschitat(self):
        self.tablitsa.delete(*self.tablitsa.get_children())
        try:
            p = self.parametry()
        except ValueError:
            p = None  # число ещё не допечатали
        if p and self.tovary:
            stavki.NDS_STAVKA = p["nds"]
            stavki.VAL_NAZV = p["val_nazv"]
            raschet(self.tovary, p["kurs"], p["dostavka"], p["sbor"], p["prochie"],
                      p["platelshik"], p["natsenka"], p["nalog"], p["vverh"])
        self.podpis_itogov.config(text=f"Суммы в: {p['val_nazv'] if p else '—'}")

        poschitano = p is not None and all("sebestoimost" in t for t in self.tovary)
        for i, t in enumerate(self.tovary):
            t["rashody"] = t.get("sbor", Decimal("0")) + t.get("prochie", Decimal("0"))
            t["poshl_akciz"] = t.get("poshlina", Decimal("0")) + t.get("akciz", Decimal("0"))
            stroka = []
            for kl, *_ in self.kolonki:
                znach = t.get(kl, "")
                if kl == "naimenovanie" and t.get("vid") == "usluga":
                    stroka.append(f"Услуга: {znach}")
                elif kl in ("naimenovanie", "strana", "kolichestvo", "tsena"):
                    stroka.append(str(znach))
                else:
                    stroka.append(som(znach) if poschitano and znach != "" else "—")
            self.tablitsa.insert("", "end", iid=str(i), values=stroka,
                                 tags=("chet",) if i % 2 else ())

        for kl, lbl in self.itogi.items():
            summa = sum(t.get(kl, Decimal("0")) for t in self.tovary) if poschitano \
                else Decimal("0")
            lbl.config(text=som(summa))
        vyr = sum(t.get("vyruchka", Decimal("0")) for t in self.tovary) if poschitano else 0
        if vyr:
            pr = sum(t["pribyl"] for t in self.tovary)
            self.marzha.config(text=f"маржа {pr / vyr * 100:.1f}% от выручки")
        else:
            self.marzha.config(text="")

    def udalit(self):
        vybrano = sorted((int(x) for x in self.tablitsa.selection()), reverse=True)
        if not vybrano:
            messagebox.showinfo("Удаление", "Выделите строку в таблице")
            return
        for i in vybrano:
            del self.tovary[i]
        self.pereschitat()

    def ochistit(self):
        if self.tovary and messagebox.askyesno("Очистить", "Удалить все товары?"):
            self.tovary.clear()
            self.pereschitat()

    def excel(self):
        if not self.tovary:
            messagebox.showinfo("Excel", "Сначала добавьте товары")
            return
        try:
            p = self.parametry()
        except ValueError as oshibka:
            messagebox.showwarning("Проверьте данные", str(oshibka))
            return
        put = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile=f"raschet_{datetime.now():%Y-%m-%d_%H-%M}.xlsx")
        if not put:
            return
        shapka = [
            ["Расчёт себестоимости импорта", datetime.now().strftime("%d.%m.%Y %H:%M")],
            ["Валюта", p["valyuta"], "Курс", float(p["kurs"]), "Суммы в", p["val_nazv"]],
            ["Тамож. сбор, %", float(p["sbor"])],
            ["НДС, %", float(p["nds"]), "Плательщик НДС",
             "да" if p["platelshik"] else "нет"],
            ["Наценка, %", float(p["natsenka"]), "Налог с выручки, %", float(p["nalog"])],
        ]
        try:
            sohranit_excel(self.tovary, shapka, put)
        except PermissionError:
            messagebox.showerror("Excel", "Файл открыт в Excel — закройте его и повторите")
            return
        messagebox.showinfo("Excel", f"Сохранено:\n{put}")


if __name__ == "__main__":
    Prilozhenie().mainloop()
