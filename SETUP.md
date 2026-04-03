# Setup

## 1. Create the environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure credentials

```bash
cp .env.example .env
```

Required:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Optional for experimental voice playback:

```bash
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
```

## 3. Run the product

CLI:

```bash
./start.sh
```

Web:

```bash
./start_web.sh
```

Direct commands:

```bash
python main.py --help
uvicorn web.app:app --reload --port 5001
```

## 4. Verify

```bash
python3 -m pytest
```

The web UI is served at [http://localhost:5001](http://localhost:5001).
