"""Main-window sidebar section builder."""

import customtkinter as ctk

from mineai import __version__
from mineai.constants import LANGUAGES, MC_VERSIONS
from mineai.gui.style import ToolTip


def build_sidebar_project(self) -> None:
    header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
    header.pack(fill="x", padx=12, pady=(8, 8))

    self.btn_settings = ctk.CTkButton(
        header,
        text="⚙",
        width=38,
        height=38,
        corner_radius=12,
        fg_color=self._button_subtle(),
        hover_color=self._button_subtle_hover(),
        text_color="#e8efff",
        command=self._open_settings,
    )
    self.btn_settings.pack(side="right")
    ToolTip(
        self.btn_settings,
        "Настройки",
        "Открывает настройки: пути KoboldCPP, OpenRouter, повторы ИИ, потоки Google, DeepL API и поведение программы.",
    )

    title_box = ctk.CTkFrame(header, fg_color="transparent")
    title_box.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        title_box,
        text="MineAI Translator",
        font=self._font_hero,
        text_color=self._strong_text(),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title_box,
        text=f"{__version__.strip()} · умная локализация сборок",
        font=self._font_small,
        text_color=self._muted_text(),
    ).pack(anchor="w")

    # Проект
    body = self._make_card(
        self.sidebar,
        "Проект",
        tip_title="Папка Minecraft",
        tip_text="Выбери папку Minecraft, где лежат mods, config, resourcepacks и save. Программа будет искать переводимые файлы именно там.",
    )

    self._field_label(
        body,
        "Папка Minecraft",
        tip_title="Папка Minecraft",
        tip_text="Это корневая папка игры или сборки. В режиме Resource Pack оригинальные .jar файлы модов не изменяются.",
    )

    self.lbl_folder = ctk.CTkLabel(
        body,
        text="Не выбрана",
        font=self._font_small,
        text_color=self._muted_text(),
        anchor="w",
        justify="left",
        wraplength=300,
    )
    self.lbl_folder.pack(fill="x", pady=(2, 6))

    btn_folder = ctk.CTkButton(
        body,
        text="📁 Выбрать папку",
        height=30,
        corner_radius=10,
        fg_color=self._button_subtle(),
        hover_color=self._button_subtle_hover(),
        text_color="#e8efff",
        command=self._select_folder,
    )
    btn_folder.pack(fill="x")
    ToolTip(
        btn_folder,
        "Выбрать папку",
        "Укажи папку Minecraft. Обычно это папка с mods/, config/ и resourcepacks/.",
    )

    # Язык и версия
    body = self._make_card(
        self.sidebar,
        "Язык и версия",
        tip_title="Целевой язык и версия игры",
        tip_text="Язык — во что переводим. Версия игры нужна для правильного pack_format у ресурс-пака и дата-пака.",
    )

    self._field_label(
        body,
        "Целевой язык",
        tip_title="Целевой язык",
        tip_text="Все переведённые строки будут проверяться на наличие символов выбранного языка.",
    )

    self.var_lang = ctk.StringVar(value=self._pref("language", "Русский"))
    lang_menu = ctk.CTkOptionMenu(
        body,
        variable=self.var_lang,
        values=list(LANGUAGES.keys()),
        height=30,
    )
    lang_menu.pack(fill="x", pady=(0, 8))
    ToolTip(
        lang_menu,
        "Целевой язык",
        "Поддерживается 11 языков: русский, испанский, немецкий, французский, китайский, японский, корейский, португальский, итальянский, польский и английский UK.",
    )

    self._field_label(
        body,
        "Версия игры",
        tip_title="Версия Minecraft",
        tip_text="Нужна для корректного pack_format в pack.mcmeta. Если не знаешь, выбери версию сборки.",
    )

    self.var_mc_ver = ctk.StringVar(value=self._pref("mc_version", "1.20.1"))
    ver_menu = ctk.CTkOptionMenu(
        body,
        variable=self.var_mc_ver,
        values=MC_VERSIONS,
        height=30,
    )
    ver_menu.pack(fill="x")
    ToolTip(
        ver_menu,
        "Версия Minecraft",
        "Определяет технический формат ресурс-пака и дата-пака.",
    )

    # Сохранение результата
    body = self._make_card(
        self.sidebar,
        "Сохранение результата",
        tip_title="Метод сохранения",
        tip_text="Resource Pack + Data Pack — безопасный режим. Inplace перезаписывает .jar модов и может сломать подписи.",
    )

    self.var_output = ctk.StringVar(value=self._pref("output_mode", "resourcepack"))

    self._radio_row(
        body,
        "Resource Pack + Data Pack",
        self.var_output,
        "resourcepack",
        command=self._update_output_ui,
        tip_title="Resource Pack + Data Pack",
        tip_text="Создаёт zip-архивы в resourcepacks и config/openloader/data. Оригинальные моды не трогаются.",
    )

    self._radio_row(
        body,
        "Перезаписать .jar (inplace)",
        self.var_output,
        "inplace",
        command=self._update_output_ui,
        tip_title="Inplace",
        tip_text="Перезаписывает файлы прямо внутри .jar модов. Может ломать подписи и вызывать предупреждения игры.",
    )

    self._field_label(
        body,
        "Имя архивов",
        tip_title="Имя архивов",
        tip_text="Имя для создаваемых zip-файлов. Если файл уже существует, программа создаст копию с номером.",
    )

    self.entry_rp_name = ctk.CTkEntry(
        body,
        placeholder_text="MineAI_Pack",
        height=30,
        corner_radius=10,
    )
    self.entry_rp_name.insert(0, self._pref("pack_name", "MineAI_Pack"))
    self.entry_rp_name.pack(fill="x")
    ToolTip(
        self.entry_rp_name,
        "Имя архивов",
        "Например: My_Modpack_RU. Итоговые файлы будут My_Modpack_RU.zip и My_Modpack_RU_Datapack.zip.",
    )

    # Что переводим
    body = self._make_card(
        self.sidebar,
        "Что переводим",
        tip_title="Области перевода",
        tip_text="Выбери, какие части сборки нужно переводить: интерфейсы модов, справочники/книги и квесты.",
    )

    self.var_mods = ctk.BooleanVar(value=self._pref_bool("translate_mods", True))
    self.var_books = ctk.BooleanVar(value=self._pref_bool("translate_books", True))
    self.var_quests = ctk.BooleanVar(value=self._pref_bool("translate_quests", True))

    self._check_row(
        body,
        "Интерфейс модов",
        self.var_mods,
        "Интерфейс модов",
        "Переводит стандартные языковые файлы модов: en_us.json -> ru_ru.json и т.п.",
    )

    self._check_row(
        body,
        "Справочники и исследования",
        self.var_books,
        "Справочники и книги",
        "Переводит книги Patchouli, JSON-справочники, MD-книги и research-файлы, если они поддерживаются.",
    )

    self._check_row(
        body,
        "Квесты (FTB + KubeJS + BQ)",
        self.var_quests,
        "Квесты",
        "Переводит FTB Quests (.snbt), KubeJS-словари и BetterQuesting JSON-файлы.",
    )
