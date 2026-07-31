# 💼 LinkedIn Translator 💀

Paste an overdramatic LinkedIn post, get a sarcastic one-line translation
of what the author actually means. Built with Streamlit + a Hugging Face
router (Qwen2.5-7B-Instruct).

## Run locally

1. Clone the repo and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Get a Hugging Face token from https://huggingface.co/settings/tokens
   (Read access is enough).

3. Either:
   - paste the token directly into the app's sidebar when it's running, or
   - set it as an environment variable so it auto-fills:

     ```bash
     export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
     ```

   - or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
     and put your token there (this file is gitignored, never committed).

4. Run the app:

   ```bash
   streamlit run main.py
   ```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (public or private).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "Create app", pick this repo, branch `main`, file `main.py`.
4. Optional: set a custom subdomain under "App URL".
5. Under app **Settings → Secrets**, add:

   ```toml
   HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxx"
   ```

6. Deploy. Your API key never touches the repo itself.

## Project structure

```
.
├── main.py                          # the Streamlit app
├── requirements.txt                 # dependencies
├── .gitignore                       # keeps secrets/junk out of git
└── .streamlit/
    └── secrets.toml.example         # template — copy to secrets.toml locally
```
