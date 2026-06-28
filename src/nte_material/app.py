"""Tkinter GUI 本体。

タブ構成:
  [育成計画] キャラごとの素材選択・進捗入力 → 残り素材を集計
  [所持リソース] 各素材の所持数を管理（直接書き換え / 一定数の増減 / 追加・削除）

集計は「残り（必要数の合計）・所持・不足（残り−所持）」を表示する。
編集のたびに自動保存（JSON）。
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from . import gamedata as gd
from . import storage
from .icons import IconManager
from .models import Character, Project


class App(ttk.Frame):
    def __init__(self, master: tk.Tk, save_path: Path = storage.DEFAULT_PATH) -> None:
        super().__init__(master, padding=8)
        self.master = master
        self.save_path = save_path
        self.project: Project = storage.load(save_path)
        self._loading = False  # 編集欄ロード中の自動保存抑止
        self.icons = IconManager()

        # アイコン(24px)が収まる行高に
        ttk.Style().configure("Treeview", rowheight=28)

        master.title("NtE 素材管理ツール")
        master.geometry("1240x720")
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.plan_tab = ttk.Frame(self.notebook, padding=6)
        self.inv_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.plan_tab, text="育成計画")
        self.notebook.add(self.inv_tab, text="所持リソース")

        self._build_plan_tab()
        self._build_inventory_tab()
        self._build_statusbar()

        self.refresh_character_list()
        self.update_summary()

    # ================================================================ 育成計画タブ
    def _build_plan_tab(self) -> None:
        tab = self.plan_tab
        tab.columnconfigure(1, weight=1)
        tab.columnconfigure(2, weight=1)
        tab.rowconfigure(0, weight=1)
        self._build_character_panel(tab)
        self._build_editor_panel(tab)
        self._build_summary_panel(tab)

    def _build_character_panel(self, parent: tk.Misc) -> None:
        frame = ttk.LabelFrame(parent, text="キャラクター", padding=6)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.char_list = tk.Listbox(frame, exportselection=False, width=18)
        self.char_list.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.char_list.bind("<<ListboxSelect>>", lambda _e: self.on_select_character())

        ttk.Button(frame, text="追加", command=self.add_character).grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )
        ttk.Button(frame, text="削除", command=self.remove_character).grid(
            row=1, column=1, sticky="ew", pady=(6, 0)
        )

    def _build_editor_panel(self, parent: tk.Misc) -> None:
        outer = ttk.Frame(parent)
        outer.grid(row=0, column=1, sticky="nsew", padx=(0, 6))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        mats = ttk.LabelFrame(outer, text="素材の種類（このキャラが使う素材）", padding=6)
        mats.grid(row=0, column=0, sticky="nsew")
        mats.columnconfigure(1, weight=1)
        self.cb_ikusei = self._combo(mats, 0, "育成素材ライン(本体)", list(gd.IKUSEI_LINES))
        self.cb_hunt = self._combo(mats, 1, "異象狩り素材", list(gd.HUNT_MATERIALS))
        self.cb_card = self._combo(mats, 2, "カード", list(gd.CARD_ROWS))
        self.cb_pilgrimage = self._combo(mats, 3, "異象巡礼", list(gd.PILGRIMAGE_MATERIALS))
        self.cb_arc_special = self._combo(mats, 4, "弧盤: 専用素材", list(gd.ARC_SPECIAL_ROWS))
        self.cb_arc_ikusei = self._combo(mats, 5, "弧盤: 育成素材ライン", list(gd.IKUSEI_LINES))

        prog = ttk.LabelFrame(outer, text="進捗（現在の状況）", padding=6)
        prog.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        prog.columnconfigure(1, weight=1)

        levels = [str(v) for v in gd.LEVEL_OPTIONS]
        self.var_include_ascension = tk.BooleanVar(value=True)
        self.var_include_skill = tk.BooleanVar(value=True)
        self.var_include_arc = tk.BooleanVar(value=True)

        self.cb_ascension = self._combo(prog, 0, "最大レベル", levels)
        ttk.Checkbutton(
            prog, text="集計に含める", variable=self.var_include_ascension, command=self.on_edit
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        self.cb_arc_level = self._combo(prog, 1, "弧盤レベル", levels)
        ttk.Checkbutton(
            prog, text="集計に含める", variable=self.var_include_arc, command=self.on_edit
        ).grid(row=1, column=2, sticky="w", padx=(8, 0))

        ttk.Separator(prog).grid(row=3, column=0, columnspan=3, sticky="ew", pady=4)
        skill_hdr = ttk.Frame(prog)
        skill_hdr.grid(row=4, column=0, columnspan=3, sticky="w")
        ttk.Label(skill_hdr, text="スキルレベル (1〜10)").pack(side="left")
        ttk.Checkbutton(
            skill_hdr, text="集計に含める", variable=self.var_include_skill, command=self.on_edit
        ).pack(side="left", padx=(8, 0))
        self.skill_vars: dict[str, tk.IntVar] = {}
        for i, skill in enumerate(gd.SKILLS):
            ttk.Label(prog, text=skill).grid(row=5 + i, column=0, sticky="w", padx=(8, 0))
            var = tk.IntVar(value=1)
            spin = ttk.Spinbox(
                prog, from_=1, to=gd.SKILL_MAX, width=5, textvariable=var, command=self.on_edit
            )
            spin.grid(row=5 + i, column=1, sticky="w")
            spin.bind("<KeyRelease>", lambda _e: self.on_edit())
            self.skill_vars[skill] = var

        ttk.Label(prog, text="サポート追加パッシブ（開放済みでチェック）").grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )
        self.support_vars: dict[str, tk.BooleanVar] = {}
        for i, (name, step) in enumerate(gd.SUPPORT_PASSIVES.items()):
            cr, cq = step["card"]
            label = f"{name}（{cr}カード×{cq}＋巡礼×{step.get('pilgrimage', 0)}）"
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(prog, text=label, variable=var, command=self.on_edit).grid(
                row=10 + i, column=0, columnspan=2, sticky="w", padx=(8, 0)
            )
            self.support_vars[name] = var

    def _combo(self, parent: tk.Misc, row: int, label: str, values: list[str]) -> ttk.Combobox:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 6))
        cb = ttk.Combobox(parent, values=values, state="readonly", width=24)
        cb.grid(row=row, column=1, sticky="ew", pady=2)
        cb.bind("<<ComboboxSelected>>", lambda _e: self.on_edit())
        return cb

    def _build_summary_panel(self, parent: tk.Misc) -> None:
        frame = ttk.LabelFrame(parent, text="残り素材の集計", padding=6)
        frame.grid(row=0, column=2, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)

        ttk.Label(frame, text="このキャラの残り素材").grid(row=0, column=0, sticky="w")
        self.char_sum_tree = ttk.Treeview(
            frame, columns=("qty",), show="tree headings", height=10
        )
        self.char_sum_tree.heading("#0", text="素材名")
        self.char_sum_tree.heading("qty", text="残り")
        self.char_sum_tree.column("#0", width=210)
        self.char_sum_tree.column("qty", width=60, anchor="e")
        self.char_sum_tree.grid(row=1, column=0, sticky="nsew", pady=(2, 8))

        ttk.Label(frame, text="全キャラ合計（残り / 所持 / 不足）").grid(row=2, column=0, sticky="w")
        self.total_sum_tree = ttk.Treeview(
            frame, columns=("rem", "own", "short"), show="tree headings", height=12
        )
        self.total_sum_tree.heading("#0", text="素材名")
        self.total_sum_tree.column("#0", width=200)
        for col, text, w in (("rem", "残り", 55), ("own", "所持", 55), ("short", "不足", 55)):
            self.total_sum_tree.heading(col, text=text)
            self.total_sum_tree.column(col, width=w, anchor="e")
        self.total_sum_tree.grid(row=3, column=0, sticky="nsew", pady=2)

    # ================================================================ 所持リソースタブ
    def _build_inventory_tab(self) -> None:
        tab = self.inv_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        self.inv_tree = ttk.Treeview(
            tab, columns=("own", "rem", "short"), show="tree headings", height=18
        )
        self.inv_tree.heading("#0", text="素材名")
        self.inv_tree.heading("own", text="所持")
        self.inv_tree.heading("rem", text="残り")
        self.inv_tree.heading("short", text="不足")
        self.inv_tree.column("#0", width=240)
        self.inv_tree.column("own", width=70, anchor="e")
        self.inv_tree.column("rem", width=70, anchor="e")
        self.inv_tree.column("short", width=70, anchor="e")
        self.inv_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.inv_tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.inv_tree.configure(yscrollcommand=scroll.set)
        self.inv_tree.bind("<<TreeviewSelect>>", lambda _e: self.on_inv_select())

        forms = ttk.Frame(tab, padding=(0, 8, 0, 0))
        forms.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.inv_selected_var = tk.StringVar(value="（素材を選択）")
        ttk.Label(forms, text="選択中:").grid(row=0, column=0, sticky="w")
        ttk.Label(forms, textvariable=self.inv_selected_var, width=28).grid(
            row=0, column=1, columnspan=3, sticky="w"
        )

        # 直接書き換え
        ttk.Label(forms, text="直接設定:").grid(row=1, column=0, sticky="e", pady=3)
        self.inv_set_var = tk.StringVar(value="0")
        ttk.Entry(forms, textvariable=self.inv_set_var, width=8).grid(row=1, column=1, sticky="w")
        ttk.Button(forms, text="設定", command=self.inv_set).grid(row=1, column=2, sticky="w", padx=4)

        # 一定数の調整
        ttk.Label(forms, text="調整量:").grid(row=2, column=0, sticky="e", pady=3)
        self.inv_delta_var = tk.StringVar(value="1")
        ttk.Entry(forms, textvariable=self.inv_delta_var, width=8).grid(row=2, column=1, sticky="w")
        ttk.Button(forms, text="＋", width=4, command=lambda: self.inv_adjust(+1)).grid(
            row=2, column=2, sticky="w", padx=(4, 0)
        )
        ttk.Button(forms, text="－", width=4, command=lambda: self.inv_adjust(-1)).grid(
            row=2, column=3, sticky="w", padx=2
        )

        # 追加・削除
        ttk.Label(forms, text="新規素材:").grid(row=3, column=0, sticky="e", pady=3)
        self.inv_new_var = tk.StringVar()
        ttk.Entry(forms, textvariable=self.inv_new_var, width=20).grid(row=3, column=1, sticky="w")
        ttk.Button(forms, text="追加", command=self.inv_add).grid(row=3, column=2, sticky="w", padx=4)
        ttk.Button(forms, text="選択を削除", command=self.inv_delete).grid(
            row=3, column=3, sticky="w"
        )

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(value=f"保存先: {self.save_path}")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )

    # ================================================================ ヘルパ
    def current_character(self) -> Character | None:
        sel = self.char_list.curselection()
        if not sel:
            return None
        return self.project.characters[sel[0]]

    def save(self) -> None:
        storage.save(self.project, self.save_path)
        self.status_var.set(f"保存しました: {self.save_path}")

    # ================================================================ キャラ操作
    def refresh_character_list(self) -> None:
        self.char_list.delete(0, tk.END)
        for ch in self.project.characters:
            self.char_list.insert(tk.END, ch.name)

    def add_character(self) -> None:
        name = simpledialog.askstring("キャラ追加", "キャラクター名:", parent=self.master)
        if not name or not name.strip():
            return
        name = name.strip()
        if self.project.get_character(name) is not None:
            messagebox.showwarning("重複", f"「{name}」は既に存在します。")
            return
        self.project.characters.append(Character.new(name))
        self.refresh_character_list()
        self.char_list.selection_clear(0, tk.END)
        self.char_list.selection_set(tk.END)
        self.on_select_character()
        self.save()

    def remove_character(self) -> None:
        ch = self.current_character()
        if ch is None:
            return
        if not messagebox.askyesno("削除確認", f"「{ch.name}」を削除しますか？"):
            return
        self.project.characters.remove(ch)
        self.refresh_character_list()
        self.update_summary()
        self.save()

    def on_select_character(self) -> None:
        ch = self.current_character()
        if ch is None:
            return
        self.load_character_to_editor(ch)
        self.update_summary()

    # ================================================================ 編集 ⇄ モデル
    def load_character_to_editor(self, ch: Character) -> None:
        self._loading = True
        try:
            self.cb_ikusei.set(ch.ikusei_line)
            self.cb_arc_ikusei.set(ch.arc_ikusei_line)
            self.cb_hunt.set(ch.hunt_mat)
            self.cb_card.set(ch.card_row)
            self.cb_pilgrimage.set(ch.pilgrimage_mat)
            self.cb_arc_special.set(ch.arc_special_row)
            self.cb_ascension.set(str(ch.ascension_level))
            self.cb_arc_level.set(str(ch.arc_level))
            self.var_include_ascension.set(ch.include_ascension)
            self.var_include_skill.set(ch.include_skill)
            self.var_include_arc.set(ch.include_arc)
            for sk, var in self.skill_vars.items():
                var.set(ch.skill_levels.get(sk, 1))
            for sk, var in self.support_vars.items():
                var.set(ch.support_done.get(sk, False))
        finally:
            self._loading = False

    def on_edit(self) -> None:
        if self._loading:
            return
        ch = self.current_character()
        if ch is None:
            return
        ch.ikusei_line = self.cb_ikusei.get()
        ch.arc_ikusei_line = self.cb_arc_ikusei.get()
        ch.hunt_mat = self.cb_hunt.get()
        ch.card_row = self.cb_card.get()
        ch.pilgrimage_mat = self.cb_pilgrimage.get()
        ch.arc_special_row = self.cb_arc_special.get()
        ch.ascension_level = self._int(self.cb_ascension.get(), ch.ascension_level)
        ch.arc_level = self._int(self.cb_arc_level.get(), ch.arc_level)
        ch.include_ascension = bool(self.var_include_ascension.get())
        ch.include_skill = bool(self.var_include_skill.get())
        ch.include_arc = bool(self.var_include_arc.get())
        for sk, var in self.skill_vars.items():
            try:
                ch.skill_levels[sk] = max(1, min(gd.SKILL_MAX, int(var.get())))
            except (tk.TclError, ValueError):
                continue
        for sk, var in self.support_vars.items():
            ch.support_done[sk] = bool(var.get())
        self.update_summary()
        self.save()

    @staticmethod
    def _int(text: str, fallback: int) -> int:
        try:
            return int(text)
        except (ValueError, TypeError):
            return fallback

    # ================================================================ 所持リソース操作
    def selected_material(self) -> str | None:
        sel = self.inv_tree.selection()
        return sel[0] if sel else None

    def on_inv_select(self) -> None:
        mat = self.selected_material()
        if mat is None:
            return
        self.inv_selected_var.set(mat)
        self.inv_set_var.set(str(self.project.owned(mat)))

    def inv_set(self) -> None:
        mat = self.selected_material()
        if mat is None:
            messagebox.showinfo("情報", "素材を選択してください。")
            return
        try:
            qty = int(self.inv_set_var.get())
        except ValueError:
            messagebox.showwarning("入力エラー", "整数を入力してください。")
            return
        self.project.set_owned(mat, qty)
        self._after_inv_change(mat)

    def inv_adjust(self, sign: int) -> None:
        mat = self.selected_material()
        if mat is None:
            messagebox.showinfo("情報", "素材を選択してください。")
            return
        try:
            delta = int(self.inv_delta_var.get())
        except ValueError:
            messagebox.showwarning("入力エラー", "調整量は整数で入力してください。")
            return
        self.project.adjust_owned(mat, sign * delta)
        self._after_inv_change(mat)

    def inv_add(self) -> None:
        name = self.inv_new_var.get().strip()
        if not name:
            return
        if name not in self.project.inventory:
            self.project.set_owned(name, 0)
        self.inv_new_var.set("")
        self._after_inv_change(name)

    def inv_delete(self) -> None:
        mat = self.selected_material()
        if mat is None:
            return
        if not messagebox.askyesno("削除確認", f"「{mat}」を所持リストから削除しますか？"):
            return
        self.project.remove_material(mat)
        self._after_inv_change(None)

    def _after_inv_change(self, select: str | None) -> None:
        self.update_summary()
        self.save()
        if select and self.inv_tree.exists(select):
            self.inv_tree.selection_set(select)
            self.inv_tree.see(select)
            self.on_inv_select()

    # ================================================================ 集計表示
    def update_summary(self) -> None:
        # このキャラの残り
        ch = self.current_character()
        self.char_sum_tree.delete(*self.char_sum_tree.get_children())
        if ch:
            rem = ch.remaining()
            for material in sorted(rem, key=gd.sort_key):
                self.char_sum_tree.insert(
                    "", tk.END, text=material, image=self.icons.get(material),
                    values=(rem[material],),
                )

        # 全体（残り/所持/不足）
        rows = self.project.material_rows()
        self.total_sum_tree.delete(*self.total_sum_tree.get_children())
        for name, rem, own, short in rows:
            if rem or own:  # 残りも所持も0の素材は出さない
                self.total_sum_tree.insert(
                    "", tk.END, text=name, image=self.icons.get(name), values=(rem, own, short)
                )

        # 所持タブのツリー（全素材を表示）
        sel = self.selected_material()
        self.inv_tree.delete(*self.inv_tree.get_children())
        for name, rem, own, short in rows:
            self.inv_tree.insert(
                "", tk.END, iid=name, text=name, image=self.icons.get(name),
                values=(own, rem, short),
            )
        if sel and self.inv_tree.exists(sel):
            self.inv_tree.selection_set(sel)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
