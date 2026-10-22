import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.io as pio
from plotly.express import colors as px_colors
import io
import base64
from pathlib import Path
import openpyxl
from io import BytesIO
from scipy import stats
# --- Additional imports for report generation ---
from fpdf import FPDF
import base64

# --- GitHub integration for saving reports ---
# Optional GitHub integration
try:
    from github import Github
    has_github = True
except ModuleNotFoundError:
    has_github = False
    st.warning(
        "PyGithub не установлен: функции сохранения в GitHub отключены."
    )

ASSETS_DIR = Path(__file__).parent / "assets"
st.set_page_config(layout="wide", page_icon=str(ASSETS_DIR / "favicon.svg"))
# Kachkin brand: logo in the sidebar header (32px, links to kachkin.pro) and the "a Kachkin tool" credit
st.logo(str(ASSETS_DIR / "kachkin-horizontal-en-ink.svg"), size="large", link="https://kachkin.pro")
st.sidebar.markdown("[a Kachkin tool](https://kachkin.pro)")


# --- Public mode: cloud saving only when keys are present in Streamlit secrets ---
# Without [github] in secrets.toml the app works without login and cloud storage:
# sessions, annotations and reports are saved as files on the user's computer.
def has_secret(section: str) -> bool:
    try:
        return section in st.secrets
    except Exception:  # no secrets.toml at all
        return False

has_github = has_github and has_secret("github")

# --- Example data (synthetic, see examples/make_demo.py) ---
EXAMPLES_DIR = Path(__file__).parent / "examples"
FONTS_DIR = Path(__file__).parent / "fonts"
DEMO_RUN = "demo_96well.txt"

# --- GitHub initialization ---
@st.cache_resource
def init_github():
    token = st.secrets["github"]["token"]
    return Github(token)

# --- GitHub helper must be defined before use ---
if has_github:
    gh = init_github()
    repo = gh.get_repo(st.secrets["github"]["repo_name"])
    def save_file_to_repo(path: str, content: bytes, commit_msg: str):
        try:
            existing = repo.get_contents(path)
            repo.update_file(path, commit_msg, content, existing.sha)
        except:
            repo.create_file(path, commit_msg, content)
# --- Выбор языка / Language selector (русский по умолчанию) ---
lang = st.sidebar.selectbox("Language / Язык", ["Русский", "English"], index=0)
# Переводы интерфейса и отчётов. Значения в данных (роли, тип планшета) остаются английскими —
# так старые сессии и разметки читаются на любом языке; здесь только их подписи.
translations = {
    "Русский": {
        "title": "qPioneer: анализ qPCR",
        "markup_header": "Разметка",
        "upload_markup": "Загрузить разметку (JSON)",
        "markup_loaded": "Разметка загружена",
        "markup_load_error": "Не удалось загрузить разметку",
        "save_markup_button": "Сохранить разметку",
        "restore_session_button": "Восстановить сессию",
        "download_markup_json": "Скачать разметку (JSON)",
        "load_header": "Данные qPCR",
        "load_prompt": "Выберите файл с данными qPCR",
        "load_info": "Загрузите файл или нажмите «Загрузить пример».",
        "load_error_cols": "В файле должны быть колонки 'Pos' и 'Cp'",
        "load_success": "Загружено лунок: {n}.",
        "settings_header": "Настройки",
        "run_id_label": "ID запуска (Run ID)",
        "plate_type_label": "Тип планшета",
        "font_size_label": "Размер шрифта на схеме планшета",
        "tab1": "1. Гены",
        "tab2": "2. Условия и повторы",
        "step1_header": "Шаг 1: гены",
        "role_label": "Роль",
        "gene_label": "Ген",
        "select_region_genes": "Область лунок для гена",
        "add_region_genes": "Назначить ген области",
        "step2_header": "Шаг 2: условия и повторы",
        "template_label": "Условие (образец)",
        "replicate_label": "Номер повтора",
        "select_region_reps": "Область лунок для условия",
        "add_region_reps": "Назначить условие и повтор",
        "status": "Разметка планшета",
        "calc_expression": "Рассчитать экспрессию",
        "results_header": "Результаты: экспрессия",
        "download_csv": "Скачать CSV",
        "download_json": "Скачать JSON",
        "download_excel": "Скачать Excel",
        "boxplot_header": "Диаграммы размаха по условиям и генам",
        "download_boxplot": "Скачать boxplot_{g}.png",
        "barplot_header": "Столбчатые диаграммы (среднее ± SD)",
        "download_barplot": "Скачать barplot_{g}.png",
        "boxplot_title": "{g}: диаграмма размаха",
        "barplot_title": "{g}: среднее ± SD",
        "expression_axis": "экспрессия (2^−ΔCt)",
        "kaleido_warning": "Для скачивания PNG установите kaleido (`pip install kaleido`).",
        "select_region_from": "От (левый верхний угол)",
        "select_region_to": "До (правый нижний угол)",
        "file_format_header": "Формат файла и колонки",
        "delimiter_label": "Разделитель",
        "delim_names": {"\t": "Табуляция", ",": "Запятая", ";": "Точка с запятой", " ": "Пробел"},
        "skiprows_label": "Пропустить строк в начале",
        "pos_col_label": "Колонка с позицией лунки",
        "cp_col_label": "Колонка со значениями Ct",
        "load_error_cols_map": "В файле нет колонок '{pos}' и '{cp}'. Проверьте названия колонок и число пропускаемых строк слева.",
        "select_run": "Файл (запуск)",
        "plate_names": {"384-well": "384 лунки", "96-well": "96 лунок"},
        "role_names": {"reference gene": "референсный ген", "target gene": "целевой ген", "negative control": "отрицательный контроль"},
        "genes_assigned": "Ген «{gene}» назначен лункам: {cnt}.",
        "reps_assigned": "Условие «{template}», повтор {replicate} назначены лункам: {cnt}.",
        "rep_short": "повт.",
        "plot_type_label": "Тип графика",
        "outlier_threshold_label": "Порог выбросов (σ)",
        "qc_summary_header": "Контроль качества",
        "qc_total_wells": "Лунок в анализе",
        "qc_outliers": "Выбросы",
        "qc_pass_rate": "Прошли контроль",
        "tab_help": "Как начать",
        "help_getting_started": """
**Как начать работу**

1. Загрузите файл qPCR (TXT/CSV/XLSX) или нажмите «Загрузить пример».
2. При необходимости настройте формат: разделитель, строки заголовка, колонки.
3. Разметьте лунки на вкладках «Гены» и «Условия и повторы».
4. Задайте порог выбросов и нажмите «Рассчитать экспрессию».
5. Посмотрите контроль качества и графики, скачайте результаты и отчёт.

Сессию можно сохранить файлом и продолжить позже.
""",
        "help_delimiter": "Разделитель колонок в TXT-файле (CSV всегда читается через запятую).",
        "help_skiprows": "Сколько строк перед заголовком таблицы пропустить.",
        "help_pos_col": "Название колонки с позицией лунки (например, A1).",
        "help_cp_col": "Название колонки со значениями Ct (Cp).",
        "help_calc_expression": "Нормализация по референсному гену (ΔCt) и расчёт экспрессии 2^−ΔCt.",
        "help_plot_type": "Диаграмма размаха или столбчатая диаграмма со средним и стандартным отклонением.",
        "cloud_off": "Облачное сохранение отключено. Сохраните сессию файлом — так данные остаются у вас.",
        "load_example": "Загрузить пример",
        "help_load_example": "Синтетический планшет на 96 лунок: ACTB (референс), SOX2 и PAX6, условия Control и Treated, по 3 повтора. Разметка уже сделана — нажмите «Рассчитать экспрессию».",
        "example_loaded": "Загружен пример (синтетические данные) с готовой разметкой.",
        "clear_data": "Очистить и загрузить другой файл",
        "report_needs_results": "Сначала нажмите «Рассчитать экспрессию».",
        "session_header": "Сессия",
        "load_session": "Загрузить сессию (JSON)",
        "session_restored": "Сессия восстановлена",
        "session_load_error": "Не удалось загрузить сессию: {e}",
        "save_session": "Сохранить сессию",
        "download_session": "Скачать сессию (JSON)",
        "cloud_session_saved": "Сессия сохранена в облако (GitHub)",
        "cloud_sessions_header": "Загрузить сессию из облака (GitHub)",
        "cloud_choose_session": "Файл сессии",
        "cloud_load_session": "Загрузить сессию из GitHub",
        "cloud_session_loaded": "Сессия {name} загружена из GitHub",
        "cloud_no_sessions": "В облаке нет сохранённых сессий",
        "cloud_sessions_error": "Не удалось загрузить список сессий: {e}",
        "cloud_markup_saved": "Разметка сохранена в облако (GitHub)",
        "cloud_markups_header": "Загрузить разметку из облака (GitHub)",
        "cloud_choose_markup": "Файл разметки",
        "cloud_load_markup": "Загрузить разметку из GitHub",
        "cloud_markup_loaded": "Разметка {name} загружена из GitHub",
        "cloud_no_markups": "В облаке нет сохранённых разметок",
        "cloud_markups_error": "Не удалось загрузить список разметок: {e}",
        "report_header": "Отчёт",
        "generate_report": "Сформировать отчёт",
        "download_report_pdf": "Скачать отчёт (PDF)",
        "download_report_html": "Скачать отчёт (HTML)",
        "cloud_pdf_saved": "PDF-отчёт сохранён в GitHub",
        "cloud_html_saved": "HTML-отчёт сохранён в GitHub",
        "report_title": "Отчёт по анализу qPCR",
        "report_qc": "Контроль качества",
        "report_results": "Экспрессия",
        "report_boxplot": "Диаграмма размаха: {g}",
        "report_barplot": "Среднее ± SD: {g}",
    },
    "English": {
        "title": "qPioneer qPCR app",
        "markup_header": "Annotation",
        "upload_markup": "Load annotation (JSON)",
        "markup_loaded": "Annotation loaded",
        "markup_load_error": "Annotation load error",
        "save_markup_button": "Save annotation",
        "restore_session_button": "Restore session",
        "download_markup_json": "Download annotation JSON",
        "load_header": "Upload qPCR Data",
        "load_prompt": "Select the qPCR data file",
        "load_info": "Upload a file or click “Load example”.",
        "load_error_cols": "File must contain 'Pos' and 'Cp' columns",
        "load_success": "Successfully loaded {n} wells.",
        "settings_header": "Settings",
        "run_id_label": "Run ID",
        "plate_type_label": "Plate type",
        "font_size_label": "Font size in heatmap",
        "tab1": "1. Genes",
        "tab2": "2. Condition & Replicates",
        "step1_header": "Step 1: Assign Genes",
        "role_label": "Role",
        "gene_label": "Gene",
        "select_region_genes": "Select region (genes)",
        "add_region_genes": "Add region (genes)",
        "step2_header": "Step 2: Assign Condition & Replicates",
        "template_label": "Condition",
        "replicate_label": "Replicate number",
        "select_region_reps": "Select region (replicates)",
        "add_region_reps": "Add region (replicates)",
        "status": "Annotation Status",
        "calc_expression": "Calculate expression",
        "results_header": "Expression Results",
        "download_csv": "Download CSV",
        "download_json": "Download JSON Results",
        "download_excel": "Download Excel",
        "boxplot_header": "Expression boxplots by Condition & Gene",
        "download_boxplot": "Download {g}.png",
        "barplot_header": "Barplot with error bars",
        "download_barplot": "Download barplot_{g}.png",
        "boxplot_title": "Boxplot {g}",
        "barplot_title": "Barplot {g}",
        "expression_axis": "expression (2^−ΔCt)",
        "kaleido_warning": "Install kaleido (`pip install kaleido`) to enable downloads.",
        "select_region_from": "From (top left)",
        "select_region_to": "To (bottom right)",
        "file_format_header": "File Format & Columns",
        "delimiter_label": "Delimiter",
        "delim_names": {"\t": "Tab", ",": "Comma", ";": "Semicolon", " ": "Space"},
        "skiprows_label": "Header rows to skip",
        "pos_col_label": "Well position column",
        "cp_col_label": "Ct value column",
        "load_error_cols_map": "Columns '{pos}' and '{cp}' must exist in file",
        "select_run": "Select Run",
        "plate_names": {"384-well": "384-well", "96-well": "96-well"},
        "role_names": {"reference gene": "reference gene", "target gene": "target gene", "negative control": "negative control"},
        "genes_assigned": "{cnt} wells assigned to gene “{gene}”.",
        "reps_assigned": "{cnt} wells assigned to condition “{template}”, replicate #{replicate}.",
        "rep_short": "rep",
        "plot_type_label": "Plot type",
        "outlier_threshold_label": "Outlier threshold (σ)",
        "qc_summary_header": "QC Summary",
        "qc_total_wells": "Total wells",
        "qc_outliers": "Outliers",
        "qc_pass_rate": "Pass rate",
        "tab_help": "Getting Started",
        "help_getting_started": """
**Quickstart Guide**

1. Upload your qPCR data file (txt/csv/xlsx) or click “Load example”.
2. Configure file format: delimiter, header rows, column names.
3. Annotate wells in “Genes” and “Condition & Replicates” tabs.
4. Set outlier threshold and click “Calculate expression”.
5. Review QC summary and plots, download your results and report.

You can save the session to a file and continue later.
""",
        "help_delimiter": "Column delimiter in TXT files (CSV is always read as comma-separated).",
        "help_skiprows": "Number of header rows to skip when reading the file.",
        "help_pos_col": "Column name with well positions (e.g., A1).",
        "help_cp_col": "Column name with Ct values.",
        "help_calc_expression": "Normalize to the reference gene (ΔCt) and compute expression 2^−ΔCt.",
        "help_plot_type": "Choose chart type: boxplot or barplot with error bars.",
        "cloud_off": "Cloud saving is off. Save your session to a file — your data stays with you.",
        "load_example": "Load example",
        "help_load_example": "Synthetic 96-well plate: ACTB (reference), SOX2 and PAX6, Control and Treated, 3 replicates each. Already annotated — click “Calculate expression”.",
        "example_loaded": "Example loaded (synthetic data) with ready annotation.",
        "clear_data": "Clear and upload another file",
        "report_needs_results": "Click “Calculate expression” first.",
        "session_header": "Session",
        "load_session": "Load session (JSON)",
        "session_restored": "Session restored",
        "session_load_error": "Failed to load session: {e}",
        "save_session": "Save session",
        "download_session": "Download session (JSON)",
        "cloud_session_saved": "Session saved to the cloud (GitHub)",
        "cloud_sessions_header": "Load session from the cloud (GitHub)",
        "cloud_choose_session": "Session file",
        "cloud_load_session": "Load session from GitHub",
        "cloud_session_loaded": "Session {name} loaded from GitHub",
        "cloud_no_sessions": "No saved sessions in the cloud",
        "cloud_sessions_error": "Could not list sessions: {e}",
        "cloud_markup_saved": "Annotation saved to the cloud (GitHub)",
        "cloud_markups_header": "Load annotation from the cloud (GitHub)",
        "cloud_choose_markup": "Annotation file",
        "cloud_load_markup": "Load annotation from GitHub",
        "cloud_markup_loaded": "Annotation {name} loaded from GitHub",
        "cloud_no_markups": "No saved annotations in the cloud",
        "cloud_markups_error": "Could not list annotations: {e}",
        "report_header": "Full Report",
        "generate_report": "Generate Full Report",
        "download_report_pdf": "Download report (PDF)",
        "download_report_html": "Download report (HTML)",
        "cloud_pdf_saved": "PDF report saved to GitHub",
        "cloud_html_saved": "HTML report saved to GitHub",
        "report_title": "qPCR Analysis Report",
        "report_qc": "QC Summary",
        "report_results": "Expression Results",
        "report_boxplot": "Boxplot for gene {g}",
        "report_barplot": "Barplot for gene {g}",
    }
}
texts = translations[lang]

# --- Getting Started Expander ---
with st.sidebar.expander(texts["tab_help"], expanded=True):
    st.markdown(texts["help_getting_started"])

# --- Save / Load entire session state ---
st.sidebar.markdown(f"## {texts['session_header']}")
if not has_github:
    st.sidebar.caption(texts["cloud_off"])
# Load session
upload_gen = st.session_state.get("upload_gen", 0)
sess_file = st.sidebar.file_uploader(texts["load_session"], type=["json"], key=f"session_upload_{upload_gen}")
if sess_file:
    try:
        sess = json.loads(sess_file.read().decode("utf-8"))
        # restore all persistent keys
        for key in ("annotation", "run", "delimiter", "plate_type", "font_size", "merged_t"):
            if key in sess:
                if key == "merged_t":
                    # Restore merged_t as a pandas DataFrame
                    import pandas as _pd
                    st.session_state["merged_t"] = _pd.DataFrame(sess["merged_t"])
                else:
                    st.session_state[key] = sess[key]
        # Restore uploaded_runs if present
        if "uploaded_runs" in sess:
            st.session_state["uploaded_runs"] = {
                name: base64.b64decode(data.encode("ascii"))
                for name, data in sess["uploaded_runs"].items()
            }
        st.sidebar.success(texts["session_restored"])
        # Removed broken restore session rerun logic
        # if st.sidebar.button(texts["restore_session_button"]):
        #     raise RerunException({})
    except Exception as e:
        st.sidebar.error(texts["session_load_error"].format(e=e))


if st.sidebar.button(texts["save_session"]):
    sess = {
        "annotation": st.session_state.get("annotation", {}),
        "run": st.session_state.get("run", ""),
        "delimiter": st.session_state.get("delimiter", "\t"),
        "skip_rows": st.session_state.get("skip_rows", 1),
        "pos_col": st.session_state.get("pos_col", "Pos"),
        "cp_col": st.session_state.get("cp_col", "Cp"),
        "plate_type": st.session_state.get("plate_type", "384-well"),
        "font_size": st.session_state.get("font_size", 8),
        "merged_t": st.session_state.get("merged_t", pd.DataFrame()).to_dict("records"),
        "uploaded_runs": {
            name: base64.b64encode(data).decode("ascii")
            for name, data in st.session_state.get("uploaded_runs", {}).items()
        }
    }
    sess_json = json.dumps(sess, ensure_ascii=False).encode("utf-8")
    st.sidebar.download_button(
        texts["download_session"],
        data=sess_json,
        file_name="session.json",
        mime="application/json",
        on_click="ignore",  # keep other one-off download buttons on screen
    )
    if has_github:
        user = gh.get_user().login
        filename = f"{user}/session_{st.session_state.get('run','session')}.json"
        save_file_to_repo(filename, sess_json, f"Save session for {user}")
        st.sidebar.success(texts["cloud_session_saved"])

# --- Load session from GitHub ---
if has_github:
    st.sidebar.markdown(f"### {texts['cloud_sessions_header']}")
    try:
        user = gh.get_user().login
        # List files in the user's folder
        contents = repo.get_contents(f"{user}")
        session_files = [file.path for file in contents if file.path.startswith(f"{user}/session_") and file.path.endswith(".json")]
        if session_files:
            choice = st.sidebar.selectbox(texts["cloud_choose_session"], session_files)
            if st.sidebar.button(texts["cloud_load_session"]):
                file_content = repo.get_contents(choice)
                data = json.loads(base64.b64decode(file_content.content).decode("utf-8"))
                # restore as above
                for key in ("annotation", "run", "delimiter", "plate_type", "font_size", "merged_t"):
                    if key in data:
                        if key == "merged_t":
                            st.session_state["merged_t"] = pd.DataFrame(data["merged_t"])
                        else:
                            st.session_state[key] = data[key]
                if "uploaded_runs" in data:
                    st.session_state["uploaded_runs"] = {
                        name: base64.b64decode(bdata.encode("ascii"))
                        for name, bdata in data["uploaded_runs"].items()
                    }
                st.sidebar.success(texts["cloud_session_loaded"].format(name=choice.split('/')[-1]))
        else:
            st.sidebar.info(texts["cloud_no_sessions"])
    except Exception as e:
        st.sidebar.error(texts["cloud_sessions_error"].format(e=e))

st.title(texts["title"])

# --- Разметка: загрузка / сохранение ---
st.sidebar.header(texts["markup_header"])
# Загрузка разметки из JSON
annot_file = st.sidebar.file_uploader(texts["upload_markup"], type=["json"], key=f"annot_upload_{upload_gen}")
if annot_file:
    try:
        data = json.loads(annot_file.read().decode("utf-8"))
        st.session_state.annotation = data
        # Сразу после загрузки JSON: перекладываем старые роли в новые
        role_map = {
            'water': 'negative control',
            'reference': 'reference gene',
            'target': 'target gene'
        }
        for w, ent in st.session_state.annotation.items():
            old = ent.get('role')
            if old in role_map:
                ent['role'] = role_map[old]
            st.session_state.annotation[w] = ent
        st.sidebar.success(texts["markup_loaded"])
    except Exception as e:
        st.sidebar.error(texts["markup_load_error"] + f": {e}")

# Инициализируем, если ещё нет
if "annotation" not in st.session_state:
    st.session_state.annotation = {}

if st.sidebar.button(texts["save_markup_button"]):
    annot_json = json.dumps(st.session_state.annotation, ensure_ascii=False).encode("utf-8")
    st.sidebar.download_button(
        texts["download_markup_json"],
        data=annot_json,
        file_name="annotation.json",
        mime="application/json",
        on_click="ignore",
    )
    if has_github:
        user = gh.get_user().login
        filename = f"{user}/annotation_{st.session_state.get('run','session')}.json"
        save_file_to_repo(filename, annot_json, f"Save annotation for {user}")
        st.sidebar.success(texts["cloud_markup_saved"])

# --- Load annotation from GitHub ---
if has_github:
    st.sidebar.markdown(f"### {texts['cloud_markups_header']}")
    try:
        user = gh.get_user().login
        contents = repo.get_contents(f"{user}")
        annot_files = [
            file.path for file in contents
            if file.path.startswith(f"{user}/annotation_") and file.path.endswith(".json")
        ]
        if annot_files:
            choice_annot = st.sidebar.selectbox(texts["cloud_choose_markup"], annot_files)
            if st.sidebar.button(texts["cloud_load_markup"]):
                file_content = repo.get_contents(choice_annot)
                annot_data = json.loads(base64.b64decode(file_content.content).decode("utf-8"))
                st.session_state.annotation = annot_data
                st.sidebar.success(texts["cloud_markup_loaded"].format(name=choice_annot.split('/')[-1]))
        else:
            st.sidebar.info(texts["cloud_no_markups"])
    except Exception as e:
        st.sidebar.error(texts["cloud_markups_error"].format(e=e))


# --- File Format & Columns ---
st.sidebar.header(texts["file_format_header"])
delimiter = st.sidebar.selectbox(
    texts["delimiter_label"],
    options=["\t", ",", ";", " "],
    format_func=lambda x: texts["delim_names"][x],
    index=0,
    help=texts["help_delimiter"]
)
skip_rows = st.sidebar.number_input(
    texts["skiprows_label"],
    min_value=0, max_value=10,
    value=st.session_state.get("skip_rows", 1),
    step=1,
    key="skip_rows",
    help=texts["help_skiprows"]
)

pos_col = st.sidebar.text_input(
    texts["pos_col_label"],
    value=st.session_state.get("pos_col", "Pos"),
    key="pos_col",
    help=texts["help_pos_col"]
)
cp_col  = st.sidebar.text_input(
    texts["cp_col_label"],
    value=st.session_state.get("cp_col", "Cp"),
    key="cp_col",
    help=texts["help_cp_col"]
)


# -------------------- qPCR Data Load --------------------
st.header(texts["load_header"])
# If we already have uploaded_runs in session, skip re‑upload
if "uploaded_runs" in st.session_state and st.session_state["uploaded_runs"]:
    run_names = list(st.session_state["uploaded_runs"].keys())
    # allow selection among restored runs
    selected_run = st.sidebar.selectbox(texts["select_run"], run_names, index=0, key="run_select")
else:
    # first‑time upload
    if st.button(texts["load_example"], help=texts["help_load_example"]):
        st.session_state["uploaded_runs"] = {DEMO_RUN: (EXAMPLES_DIR / DEMO_RUN).read_bytes()}
        st.session_state.annotation = json.loads((EXAMPLES_DIR / "demo_96well_annotation.json").read_text(encoding="utf-8"))
        st.session_state["plate_type"] = "96-well"
        st.rerun()
    uploaded_files = st.file_uploader(
        texts["load_prompt"], 
        type=["txt","csv","xls","xlsx"],
        accept_multiple_files=True,
        key=f"data_upload_{upload_gen}"
    )
    if uploaded_files:
        for f in uploaded_files:
            st.session_state.setdefault("uploaded_runs", {})[f.name] = f.getvalue()
    # if still no data, prompt and exit
    if not st.session_state.get("uploaded_runs"):
        st.info(texts["load_info"])
        st.stop()
    run_names = list(st.session_state["uploaded_runs"].keys())
    selected_run = st.sidebar.selectbox(texts["select_run"], run_names, index=0, key="run_select")

if DEMO_RUN in run_names:
    st.info(texts["example_loaded"])
if st.button(texts["clear_data"]):
    for key in ("uploaded_runs", "annotation", "merged_t", "pair_pvals", "qc_summary"):
        st.session_state.pop(key, None)
    # new widget keys empty the file uploaders, otherwise they would re-add the files
    st.session_state["upload_gen"] = upload_gen + 1
    st.rerun()

# Load the chosen run from memory
raw = st.session_state["uploaded_runs"][selected_run]
uploaded = io.BytesIO(raw)
uploaded.name = selected_run

def load_df(f, sep, skip):
    ext = f.name.split(".")[-1].lower()
    if ext in ("xls", "xlsx"):
        return pd.read_excel(f, skiprows=skip)
    elif ext == "csv":
        return pd.read_csv(f, sep=",", skiprows=skip)
    else:
        return pd.read_csv(f, sep=sep, skiprows=skip)

df = load_df(uploaded, sep=delimiter, skip=skip_rows)
df.columns = df.columns.str.strip()
if not {pos_col, cp_col}.issubset(df.columns):
    st.error(texts["load_error_cols_map"].format(pos=pos_col, cp=cp_col))
    st.stop()
df["Pos"] = df[pos_col]
df["Cp"]  = df[cp_col]

df["Cp"] = df["Cp"].replace(0, np.nan)
df["row"] = df["Pos"].str[0]
df["col"] = df["Pos"].str[1:].astype(int)
df["well"] = df["row"] + df["col"].astype(str)

st.success(texts["load_success"].format(n=len(df)))
st.dataframe(df.head(), use_container_width=True)  # оставляем, не переводится

# --- Инициализация state для разметки ---
if "annotation" not in st.session_state:
    st.session_state.annotation = {}

# Сетка 384-well
rows = list("ABCDEFGHIJKLMNOP")
cols = list(range(1, 25))
wells = [f"{r}{c}" for r in rows for c in cols]

# --- Общие настройки ---
st.sidebar.markdown(f"## {texts['settings_header']}")
st.sidebar.text_input(texts["run_id_label"], key="run", value="Run1")
# -------------------- Тип планшетки --------------------
plate_type = st.sidebar.selectbox(texts["plate_type_label"], ("384-well", "96-well"), index=0, key="plate_type",
                                  format_func=lambda x: texts["plate_names"][x])

if plate_type == "384-well":
    rows = list("ABCDEFGHIJKLMNOP")
    cols = list(range(1, 25))
else:
    rows = list("ABCDEFGH")
    cols = list(range(1, 13))

wells = [f"{r}{c}" for r in rows for c in cols]
# ------------------------------------------------------
font_size = st.sidebar.slider(texts["font_size_label"], min_value=6, max_value=20, value=8, step=1)

# Вкладки для двух этапов разметки
tab1, tab2 = st.tabs([texts["tab1"], texts["tab2"]])

# -------------------- Вкладка 1: Гены --------------------
with tab1:
    st.header(texts["step1_header"])
    gene = st.text_input(texts["gene_label"], value="ACTB")
    role = st.selectbox(texts["role_label"], ["reference gene", "target gene", "negative control"],
                        format_func=lambda r: texts["role_names"][r])
    st.subheader(texts["select_region_genes"])
    c1, c2 = st.columns(2)
    start1 = c1.selectbox(texts["select_region_from"], wells, key="g_start")
    end1   = c2.selectbox(texts["select_region_to"], wells, key="g_end")
    if st.button(texts["add_region_genes"]):
        r0, c0 = start1[0], int(start1[1:])
        r1, c1n = end1[0],   int(end1[1:])
        i0, i1 = rows.index(r0), rows.index(r1)
        c0, c1n = min(c0, c1n), max(c0, c1n)
        cnt = 0
        for rr in rows[min(i0, i1): max(i0, i1) + 1]:
            for cc in range(c0, c1n + 1):
                w = f"{rr}{cc}"
                ent = st.session_state.annotation.get(w, {})
                ent.update({"gene": gene, "role": role})
                st.session_state.annotation[w] = ent
                cnt += 1
        st.success(texts["genes_assigned"].format(cnt=cnt, gene=gene))

# -------------------- Вкладка 2: Шаблон и репликаты --------------------
with tab2:
    st.header(texts["step2_header"])
    template = st.text_input(texts["template_label"], value="N4E8")
    replicate = st.text_input(texts["replicate_label"], value="1")
    st.subheader(texts["select_region_reps"])
    c3, c4 = st.columns(2)
    start2 = c3.selectbox(texts["select_region_from"], wells, key="s_start")
    end2   = c4.selectbox(texts["select_region_to"], wells, key="s_end")
    if st.button(texts["add_region_reps"]):
        r0, c0 = start2[0], int(start2[1:])
        r1, c1n = end2[0],   int(end2[1:])
        i0, i1 = rows.index(r0), rows.index(r1)
        c0, c1n = min(c0, c1n), max(c0, c1n)
        cnt = 0
        for rr in rows[min(i0, i1): max(i0, i1) + 1]:
            for cc in range(c0, c1n + 1):
                w = f"{rr}{cc}"
                ent = st.session_state.annotation.get(w, {})
                ent.update({
                    "template": template,
                    "replicate": replicate,
                    "run": st.session_state.run
                })
                st.session_state.annotation[w] = ent
                cnt += 1
        st.success(texts["reps_assigned"].format(cnt=cnt, template=template, replicate=replicate))

# -------------------- Итоговая heatmap --------------------
st.markdown("---")
st.subheader(texts["status"])

z = []
text = []
palette = {
    "negative control": "blue",
    "reference gene": "green",
    "target gene": "red"
}

for r in rows:
    for c in cols:
        w = f"{r}{c}"
        ent = st.session_state.annotation.get(w, {})
        if ent.get("role"):
            # Универсальный маппинг с учётом старых и новых ролей
            role_key = ent.get('role', '')
            map_to = {
                'negative control': 1,
                'reference gene': 2,
                'target gene': 3
            }
            z.append(map_to.get(role_key, 0))
            text.append(
                f"{ent.get('gene','')}<br>"
                f"{ent.get('template','')}<br>"
                f"{texts['rep_short']}: {ent.get('replicate','')}"
)
        else:
            z.append(0)
            text.append("")

# «len(rows)×len(cols)» вместо жёстких 16×24
z_mat    = np.array(z).reshape(len(rows), len(cols))[::-1, :]
text_mat = np.array(text).reshape(len(rows), len(cols))[::-1, :]

fig = go.Figure(go.Heatmap(
    z=z_mat,
    text=text_mat,
    hoverinfo="text",
    texttemplate="%{text}",           # показываем текст прямо в ячейках
    textfont=dict(size=font_size),    # динамический размер шрифта
    colorscale=[
        [0, "white"],
        [1/3, palette["negative control"]],
        [2/3, palette["reference gene"]],
        [1, palette["target gene"]],
    ],
    showscale=False
))
fig.update_traces(xgap=1, ygap=1)
fig.update_layout(
    height=600,
    xaxis=dict(
        tickmode="array",
        tickvals=list(range(len(cols))),
        ticktext=list(range(1, len(cols)+1))
    ),
    yaxis=dict(
        tickmode="array",
        tickvals=list(range(len(rows))),
        ticktext=rows[::-1]
    ),
    margin=dict(t=10, b=10, l=10, r=10)
)
st.plotly_chart(fig, use_container_width=True)

#
# -------------------- Расчёт экспрессии и QC --------------------
# Threshold slider for outlier detection
threshold = st.slider(
    texts["outlier_threshold_label"],
    min_value=0.0, max_value=5.0,
    value=2.0, step=0.5
)
if st.button(texts["calc_expression"], help=texts["help_calc_expression"]):
    ann_df = (
        pd.DataFrame.from_dict(st.session_state.annotation, orient="index")
          .reset_index().rename(columns={"index":"well"})
    )
    dfm = df.merge(ann_df, on="well", how="left")
    dfm = dfm[dfm["role"].isin(["reference gene","target gene"])].dropna(subset=["Cp"])
    # Outlier detection
    dfm["tech_mean"] = dfm.groupby(["template","replicate","gene","run"])["Cp"].transform("mean")
    dfm["tech_sd"]   = dfm.groupby(["template","replicate","gene","run"])["Cp"].transform("std")
    dfm["is_outlier"] = (dfm["Cp"] - dfm["tech_mean"]).abs() > threshold * dfm["tech_sd"]
    # QC summary
    total_wells = len(dfm)
    outliers    = int(dfm["is_outlier"].sum())
    pass_rate   = (total_wells - outliers) / total_wells * 100 if total_wells>0 else 0
    outlier_rate = outliers / total_wells * 100 if total_wells > 0 else 0
    st.session_state["qc_summary"] = {
        "total_wells": total_wells,
        "outliers": outliers,
        "pass_rate": pass_rate,
        "outlier_rate": outlier_rate
    }

    # 1) Среднее Cp по техническим репликам
    tech_avg = (
        dfm
        .groupby(["template","replicate","gene","run"])["Cp"]
        .mean()
        .rename("Cp_avg")
        .reset_index()
    )

    # 2) Среднее Cp по референсам
    ref_avg = (
        dfm[dfm["role"] == "reference gene"]
        .groupby(["template","run"])["Cp"]
        .mean()
        .rename("Cp_ref")
        .reset_index()
    )

    # 3) Слияние и расчёт ΔCt / expression
    merged = tech_avg.merge(ref_avg, on=["template","run"], how="left")
    merged["ΔCt"]      = merged["Cp_avg"] - merged["Cp_ref"]
    merged["expression"] = 2 ** (-merged["ΔCt"])

    # Оставляем только target-гены
    merged_t = merged[merged["gene"].isin(
        dfm[dfm["role"]=="target gene"]["gene"].unique()
    )]

    from itertools import combinations

    # Pairwise t-tests per gene, Bonferroni correction
    pair_pvals = {}
    for gene in merged_t["gene"].unique():
        subs = merged_t[merged_t["gene"] == gene]
        templates = subs["template"].unique().tolist()
        comps = list(combinations(templates, 2))
        m = len(comps)
        gene_pairs = []
        for a, b in comps:
            vals_a = subs[subs["template"] == a]["expression"]
            vals_b = subs[subs["template"] == b]["expression"]
            if len(vals_a)>1 and len(vals_b)>1:
                p = stats.ttest_ind(vals_a, vals_b, equal_var=False).pvalue
            else:
                p = None
            # Bonferroni adjust
            if p is not None:
                p_adj = min(p * m, 1.0)
            else:
                p_adj = None
            gene_pairs.append(((a, b), p_adj))
        pair_pvals[gene] = gene_pairs
    st.session_state["pair_pvals"] = pair_pvals
    st.session_state["merged_t"] = merged_t

#
# Persist merged results and allow chart selection
if "merged_t" in st.session_state:
    merged_t = st.session_state["merged_t"]

    # Let user choose plot type
    plot_type = st.radio(
        texts["plot_type_label"],
        [texts["boxplot_header"], texts["barplot_header"]],
        key="plot_type",
        help=texts["help_plot_type"]
    )

    # Always show full results including any p-values
    st.subheader(texts["results_header"])
    st.dataframe(
        merged_t,
        use_container_width=True
    )
    # --- CSV and JSON download buttons ---
    st.download_button(
        texts["download_csv"],
        data=merged_t.to_csv(index=False).encode("utf-8"),
        file_name="qpcr_expression.csv",
        mime="text/csv"
    )
    st.download_button(
        texts["download_json"],
        data=merged_t.to_json(orient="records", force_ascii=False).encode("utf-8"),
        file_name="qpcr_expression.json",
        mime="application/json"
    )
    # --- Excel export ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        merged_t.to_excel(writer, sheet_name="Expression", index=False)
        # adjust column widths
        for idx, col in enumerate(merged_t.columns, 1):
            col_letter = openpyxl.utils.get_column_letter(idx)
            writer.book.active.column_dimensions[col_letter].width = max(15, len(col) + 2)
    output.seek(0)
    st.download_button(
        texts["download_excel"],
        data=output,
        file_name="qpcr_expression.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # QC summary
    qc = st.session_state.get("qc_summary", {})
    if qc:
        st.subheader(texts["qc_summary_header"])
        st.write(f"{texts['qc_total_wells']}: {qc['total_wells']}")
        st.write(f"{texts['qc_outliers']}: {qc['outliers']} ({qc['outlier_rate']:.1f}%)")
        st.write(f"{texts['qc_pass_rate']}: {qc['pass_rate']:.1f}%")

    # Generate chart based on selection
    if plot_type == texts["boxplot_header"]:
        st.subheader(texts["boxplot_header"])
        palette = px_colors.qualitative.Plotly
        tabs = st.tabs(merged_t["gene"].unique().tolist())
        for g, tb in zip(merged_t["gene"].unique(), tabs):
            with tb:
                sub = merged_t[merged_t["gene"] == g]
                fig_b = go.Figure()
                for i, cond in enumerate(sub["template"].unique()):
                    vals = sub[sub["template"] == cond]["expression"]
                    color = palette[i % len(palette)]
                    fig_b.add_trace(go.Box(
                        y=vals, name=cond,
                        fillcolor=color, line_color=color, marker_color=color,
                        boxpoints='all', jitter=0.3, pointpos=-1.8
                    ))
                fig_b.update_layout(title=texts["boxplot_title"].format(g=g), yaxis_title=texts["expression_axis"], margin=dict(t=30,b=20))
                # Annotate pairwise significance for boxplot
                max_expr = sub["expression"].max()
                y_start = max_expr * 1.05
                h = max_expr * 0.03
                tpls = sub["template"].unique().tolist()
                for (a, b), p in st.session_state.get("pair_pvals", {}).get(g, []):
                    if p is None: continue
                    label = "*" if p < 0.05 else "ns"
                    # draw bracket
                    fig_b.add_shape(type="line",
                                    x0=a, x1=b, y0=y_start, y1=y_start,
                                    line=dict(color="red"))
                    fig_b.add_shape(type="line",
                                    x0=a, x1=a, y0=y_start, y1=y_start - h,
                                    line=dict(color="red"))
                    fig_b.add_shape(type="line",
                                    x0=b, x1=b, y0=y_start, y1=y_start - h,
                                    line=dict(color="red"))
                    # label at numeric midpoint
                    x0 = tpls.index(a)
                    x1 = tpls.index(b)
                    x_mid = (x0 + x1) / 2
                    fig_b.add_annotation(
                        x=x_mid, y=y_start + h * 1.2,
                        text=label, showarrow=False,
                        font=dict(size=16, color="red"),
                        xref="x", yref="y"
                    )
                    y_start += h * 2.5
                st.plotly_chart(fig_b, use_container_width=True)
                try:
                    img = pio.to_image(fig_b, format="png")
                    st.download_button(texts["download_boxplot"].format(g=g),
                                       data=img, file_name=f"boxplot_{g}.png", mime="image/png")
                except:
                    st.warning(texts["kaleido_warning"])
    else:
        st.subheader(texts["barplot_header"])
        tabs = st.tabs(merged_t["gene"].unique().tolist())
        for g, tb in zip(merged_t["gene"].unique(), tabs):
            with tb:
                sub = merged_t[merged_t["gene"] == g]
                stats = sub.groupby("template")["expression"].agg(["mean","std"]).reset_index()
                fig_bar = go.Figure(go.Bar(
                    x=stats["template"],
                    y=stats["mean"],
                    error_y=dict(type="data", array=stats["std"]),
                    marker_color="lightgrey"  # make bars grey instead of black
                ))
                # add scatter of raw values
                for i, cond in enumerate(stats["template"]):
                    y_vals = merged_t[(merged_t["gene"]==g) & (merged_t["template"]==cond)]["expression"]
                    fig_bar.add_trace(go.Scatter(
                        x=[cond]*len(y_vals),
                        y=y_vals,
                        mode='markers',
                        marker=dict(color='black', size=6),
                        showlegend=False
                    ))
                # Annotate pairwise significance for barplot
                max_val = stats["mean"].max()
                max_std = stats["std"].max()
                # Increase vertical offset so brackets sit higher above the error bars
                padding = max_std * 1.5
                y_start = max_val + padding
                # Use std-based height for consistent spacing
                h = max_std * 0.15
                tpls = stats["template"].tolist()
                for (a, b), p in st.session_state.get("pair_pvals", {}).get(g, []):
                    if p is None: continue
                    label = "*" if p < 0.05 else "ns"
                    # draw bracket
                    fig_bar.add_shape(type="line",
                                      x0=a, x1=b, y0=y_start, y1=y_start,
                                      line=dict(color="red"))
                    fig_bar.add_shape(type="line",
                                      x0=a, x1=a, y0=y_start, y1=y_start - h,
                                      line=dict(color="red"))
                    fig_bar.add_shape(type="line",
                                      x0=b, x1=b, y0=y_start, y1=y_start - h,
                                      line=dict(color="red"))
                    # label at numeric midpoint
                    x0 = tpls.index(a)
                    x1 = tpls.index(b)
                    x_mid = (x0 + x1) / 2
                    fig_bar.add_annotation(
                        x=x_mid, y=y_start + h * 1.8,
                        text=label, showarrow=False,
                        font=dict(size=16, color="red"),
                        xref="x", yref="y"
                    )
                    y_start += h * 3
                fig_bar.update_layout(title=texts["barplot_title"].format(g=g), yaxis_title=texts["expression_axis"], margin=dict(t=30,b=20))
                st.plotly_chart(fig_bar, use_container_width=True)
                try:
                    img = pio.to_image(fig_bar, format="png")
                    st.download_button(
                        texts["download_barplot"].format(g=g),
                        data=img,
                        file_name=f"barplot_{g}.png",
                        mime="image/png"
                    )
                except:
                    st.warning(texts["kaleido_warning"])


# -------------------- Full Report Generation --------------------
import matplotlib
# Ensure plotly can write images
import plotly.io as pio

st.sidebar.markdown(f"## {texts['report_header']}")

# Helper to save files to GitHub repository under a per-user folder
# (already defined above if has_github)

if st.sidebar.button(texts["generate_report"]):
    if st.session_state.get("merged_t", pd.DataFrame()).empty:
        st.sidebar.warning(texts["report_needs_results"])
        st.stop()
    # Create PDF with fpdf2. Embedded DejaVu fonts (fonts/) cover Cyrillic, Greek (ΔCt) and other scripts.
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("DejaVu", "", str(FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font("DejaVuMono", "", str(FONTS_DIR / "DejaVuSansMono.ttf"))
    pdf.add_page()

    def pdf_line(height, text):
        pdf.cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", size=14)
    pdf_line(10, texts["report_title"])

    # QC summary
    pdf.set_font("DejaVu", size=12)
    qc = st.session_state.get("qc_summary", {})
    pdf_line(8, f"{texts['qc_total_wells']}: {qc.get('total_wells', 0)}")
    pdf_line(8, f"{texts['qc_outliers']}: {qc.get('outliers', 0)} ({qc.get('outlier_rate', 0):.1f}%)")
    pdf.ln(4)

    # Expression table
    merged_t = st.session_state.get("merged_t", pd.DataFrame())
    pdf.set_font("DejaVuMono", size=8)
    cols = merged_t.columns.tolist()
    header = "  ".join(c[:10].ljust(10) for c in cols)
    pdf_line(5, header)
    for _, row in merged_t.iterrows():
        line = "  ".join(str(row[c])[:10].ljust(10) for c in cols)
        pdf_line(5, line)
    pdf.ln(4)

    # Generate and embed both boxplot and barplot for each gene
    for g in merged_t["gene"].unique():
        sub = merged_t[merged_t["gene"] == g]
        # --- Generate Boxplot ---
        palette = px_colors.qualitative.Plotly
        fig_box = go.Figure()
        for i, cond in enumerate(sub["template"].unique()):
            vals = sub[sub["template"] == cond]["expression"]
            color = palette[i % len(palette)]
            fig_box.add_trace(go.Box(
                y=vals, name=cond, fillcolor=color,
                line_color=color, marker_color=color,
                boxpoints='all', jitter=0.3, pointpos=-1.8
            ))
        fig_box.update_layout(title=texts["boxplot_title"].format(g=g), yaxis_title=texts["expression_axis"], margin=dict(t=30,b=20))
        # --- Generate Barplot ---
        stats_df = sub.groupby("template")["expression"].agg(["mean","std"]).reset_index()
        fig_bar = go.Figure(go.Bar(
            x=stats_df["template"], y=stats_df["mean"],
            error_y=dict(type="data", array=stats_df["std"]),
            marker_color="lightgrey"
        ))
        for cond in stats_df["template"]:
            vals = sub[sub["template"] == cond]["expression"]
            fig_bar.add_trace(go.Scatter(
                x=[cond]*len(vals), y=vals, mode="markers",
                marker=dict(color="black", size=6), showlegend=False
            ))
        fig_bar.update_layout(title=texts["barplot_title"].format(g=g), yaxis_title=texts["expression_axis"], margin=dict(t=30,b=20))

        # Render both plots in memory: user plots are never written to disk
        img_box_bytes = pio.to_image(fig_box, format="png", scale=2)
        img_bar_bytes = pio.to_image(fig_bar, format="png", scale=2)

        # Embed both images in PDF: boxplot then barplot
        pdf.ln(2)
        pdf.set_font("DejaVu", size=12)
        pdf_line(6, texts["report_boxplot"].format(g=g))
        pdf.image(io.BytesIO(img_box_bytes), w=100)
        pdf.ln(2)
        pdf_line(6, texts["report_barplot"].format(g=g))
        pdf.image(io.BytesIO(img_bar_bytes), w=100)
        pdf.ln(4)

        # Prepare HTML embed for both plots
        if "full_html_parts" not in locals():
            full_html_parts = [f"<h1>{texts['report_title']}</h1>"]
            full_html_parts.append(f"<h2>{texts['report_qc']}</h2><ul>"
                                   f"<li>{texts['qc_total_wells']}: {qc.get('total_wells',0)}</li>"
                                   f"<li>{texts['qc_outliers']}: {qc.get('outliers',0)} ({qc.get('outlier_rate',0):.1f}%)</li>"
                                   "</ul>")
            full_html_parts.append(f"<h2>{texts['report_results']}</h2>")
            full_html_parts.append(merged_t.to_html(index=False, classes='table table-striped'))
        # Boxplot HTML
        img_box_b64 = base64.b64encode(img_box_bytes).decode("utf-8")
        full_html_parts.append(f"<h2>{texts['report_boxplot'].format(g=g)}</h2>")
        full_html_parts.append(f'<img src="data:image/png;base64,{img_box_b64}" style="max-width:600px;"/>')
        # Barplot HTML
        img_bar_b64 = base64.b64encode(img_bar_bytes).decode("utf-8")
        full_html_parts.append(f"<h2>{texts['report_barplot'].format(g=g)}</h2>")
        full_html_parts.append(f'<img src="data:image/png;base64,{img_bar_b64}" style="max-width:600px;"/>')

    # Finalize PDF
    pdf_bytes = bytes(pdf.output())
    st.sidebar.download_button(
        texts["download_report_pdf"],
        data=pdf_bytes,
        file_name="qpcr_full_report.pdf",
        mime="application/pdf",
        on_click="ignore",  # the HTML button must stay after the PDF download
    )
    # Upload PDF report to GitHub Repo
    if has_github:
        save_file_to_repo(
            f"{gh.get_user().login}/qpcr_full_report.pdf",
            pdf_bytes,
            "Add full PDF report"
        )
        st.sidebar.success(texts["cloud_pdf_saved"])

    # Finalize HTML report
    # charset: without it a saved report shows Cyrillic and ΔCt as mojibake
    html_lang = "ru" if lang == "Русский" else "en"
    full_html = (f'<!doctype html><html lang="{html_lang}"><head><meta charset="utf-8"><title>{texts["report_title"]}</title></head><body>'
                 + "".join(full_html_parts) + "</body></html>")
    st.sidebar.download_button(
        texts["download_report_html"],
        data=full_html,
        file_name="qpcr_full_report.html",
        mime="text/html",
        on_click="ignore",
    )
    # Upload HTML report to GitHub Repo
    if has_github:
        save_file_to_repo(
            f"{gh.get_user().login}/qpcr_full_report.html",
            full_html,
            "Add full HTML report"
        )
        st.sidebar.success(texts["cloud_html_saved"])

# --- Add these entries to your Streamlit secrets.toml ---
# [github]
# token = "ghp_YOUR_PERSONAL_ACCESS_TOKEN"
# repo_name = "puerhmaster/qPioneer-user-data"