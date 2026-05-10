# How to Deploy RelationShit Question Generator (Free, Browser-Accessible)

## Step 1 — Push to GitHub
1. Create a new GitHub repo (e.g. `rsa-question-generator`)
2. Upload all files in this `rsa_app/` folder to the repo root:
   - `app.py`
   - `questions_db.py`
   - `requirements.txt`

## Step 2 — Deploy on Streamlit Community Cloud (FREE)
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repo, branch `main`, and file `app.py`
5. Click **"Advanced settings"** → **Secrets** → add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
6. Click **Deploy**

Your app will be live at a URL like:
`https://your-app-name.streamlit.app`

Share that URL with your entire team — no installation required.

## Using the API Key Secret (optional hardening)
To avoid entering the key in the sidebar every time, update `app.py` line ~32:

```python
api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or st.text_input(
    "Anthropic API Key", type="password", placeholder="sk-ant-..."
)
```

This auto-uses the secret in production but still allows manual entry locally.

## Running Locally
```bash
pip install streamlit anthropic
streamlit run app.py
```
