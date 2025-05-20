# qPioneer: All-in-One qPCR Analysis App

**qPioneer** is a feature-rich Streamlit application for interactive analysis of qPCR data on 96- and 384-well plates. It provides:

* **Fast Data Upload & Annotation:** Assign genes, conditions, and replicates via a visual plate layout.
* **Quality Control (QC):** Detect outliers (σ-based) and view pass/outlier rates.
* **Normalization & Expression Calculation:** Compute ΔCt and relative expression (2⁻ΔCt).
* **Statistical Testing:** Pairwise t-tests with Bonferroni correction and significance annotations.
* **Interactive Plots:** Boxplots and barplots with raw data points and significance brackets.
* **Session & Annotation Persistence:** Save and load entire sessions or annotations locally (JSON) or in the cloud (GitHub).
* **Full Report Generation:** Download a comprehensive report in PDF and HTML formats.

---

## 🚀 Features

1. **Data Upload**: Supports TXT/CSV/XLSX files with customizable delimiters, headers, and column mappings (`Pos` for well position, `Cp` for Ct values).
2. **Plate Annotation**: Intuitive two-step workflow:

   * **Step 1:** Mark wells for genes (`reference gene`, `target gene`, `negative control`).
   * **Step 2:** Mark wells for experimental conditions (templates) and replicates.
3. **QC & Analysis**:

   * Auto-detect outliers by standard deviation threshold.
   * Summarize total wells, outliers, and pass rate.
   * Normalize Ct values (ΔCt) and compute expression (2⁻ΔCt).
4. **Statistics & Visualization**:

   * Pairwise two-sample t-tests per gene with Bonferroni correction.
   * Annotated interactive Plotly charts (boxplots & barplots).
   * Dynamic download buttons for CSV, JSON, Excel, PNG charts.
5. **Session & Annotation Management**:

   * Save/restore entire session state locally via JSON.
   * Save/load annotation maps separately.
   * Optional GitHub integration: each user can save and retrieve files in their personal folder in the repo.
6. **Full Report**:

   * Generate PDF & HTML reports combining QC, tables, and plots.
   * Optional upload of reports to GitHub.

---

## 🔧 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/<your-org>/qPioneer.git
   cd qPioneer
   ```
2. **Create a Python virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux / macOS
   venv\Scripts\activate     # Windows
   ```
3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

### 1. Streamlit Secrets

Create a file `~/.streamlit/secrets.toml` (for local development) or configure **Secrets** in Streamlit Cloud with the following sections:

```toml
[gdrive_oauth]
client_config = """
{
  "installed": {
    "client_id": "...",
    "client_secret": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost"]
  }
}
"""

[gdrive_service_account]
service_account = """
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...@...iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
"""

[github_oauth]
client_id     = "<GitHub OAuth App Client ID>"
client_secret = "<GitHub OAuth App Client Secret>"

[github]
repo_name = "<GitHubUsername>/qPioneer-user-data"
```

* **gdrive\_oauth**: Used for manual OAuth flows with PyDrive2.
* **gdrive\_service\_account**: For service-account authentication (no interactive login).
* **github\_oauth**: OAuth app credentials for per-user GitHub login.
* **github\:repo\_name**: Full repo path where user files are stored.

---

## 📡 GitHub Integration

When enabled, users will be prompted to **Log in with GitHub**. After login:

* Their `login` name is used as a directory prefix.
* **Save** buttons write to `/{login}/…` in the repo.
* **Load** selectors list only files under `/{login}/…`.

This ensures **isolation**: each user sees only their own files.

---

## ▶️ Usage

1. **Run the app**:

   ```bash
   streamlit run qpcr_analyse_app.py
   ```
2. **Sidebar Workflow**:

   * **Session**: Load or save entire session state.
   * **Annotation**: Load or save plate annotations.
   * **File Format**: Configure delimiter, headers, and column names.
   * **Upload Data**: Drag & drop or browse qPCR data files.
   * **Settings**: Set Run ID, plate type (96/384), font size.
3. **Annotate**:

   * **Genes** tab: Select region, assign gene & role.
   * **Condition & Replicates** tab: Select region, assign template & replicate.
   * **Heatmap**: Visual summary of your annotation.
4. **Calculate Expression**:

   * Click **Calculate expression** → view QC metrics & expression table.
   * Download CSV/JSON/Excel.
5. **Visualize**:

   * Choose boxplot or barplot.
   * Download PNG charts.
6. **Full Report**:

   * Click **Generate Full Report** → download PDF/HTML.
   * Optionally upload reports to GitHub.

---

## 📖 Examples

**Save a session to GitHub:**

```python
if has_github:
    save_file_to_repo(
        f"{user}/session_{run_id}.json",
        sess_json,
        f"Save session for {user}" )
```

**Load session from GitHub:**

```python
contents = repo.get_contents(f"{user}")
session_files = [f.path for f in contents if f.path.startswith(f"{user}/session_")]
```

---

## 🛠️ Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/...`)
3. Commit your changes (`git commit -m "..."`)
4. Push to your branch (`git push origin feat/...`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
